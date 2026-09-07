from psycopg2 import sql

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html_escape

from .sale_order_line import fence_orders

_INTERNAL_TOKEN = object()
_FLAGS = ('course', 'batch', 'year', 'modality', 'payment')
_TECHNICAL = frozenset({
    'state', 'academic_user_id', 'academic_date', 'finance_user_id', 'finance_date',
    'refuse_user_id', 'request_attachment_id', 'final_attachment_id', 'pdf_pending',
    'irg_guard_snapshot', 'irg_guard_blocked', 'irg_guard_conflict_detail',
})
_REQUEST = frozenset({
    'student_id', 'student_course_id', 'sale_order_id',
    'change_course', 'change_batch', 'change_year', 'change_modality', 'change_payment',
    'origin_course_id', 'origin_batch_id', 'origin_year_id', 'origin_modality',
    'origin_payment_mode_id', 'dest_course_id', 'dest_batch_id', 'dest_year_id',
    'dest_modality', 'dest_payment_mode_id',
})
_PROTECTED = _TECHNICAL | _REQUEST


class GuardConflict(Exception):
    """Only business conflicts; PostgreSQL concurrency errors are never caught."""


class EnrollmentChange(models.Model):
    _inherit = 'irg.enrollment.change'

    irg_guard_snapshot = fields.Json(copy=False, readonly=True)
    irg_guard_blocked = fields.Boolean(copy=False, readonly=True)
    irg_guard_conflict_detail = fields.Text(copy=False, readonly=True)

    def _guard_internal(self, allowed):
        # JSON/RPC cannot manufacture this Python object identity. Bind scope to
        # these IDs and to the exact fields needed by this internal operation.
        return self.with_context(irg_guard_scope=(
            _INTERNAL_TOKEN, tuple(self.ids), frozenset(allowed)))

    def write(self, vals):
        protected = _PROTECTED.intersection(vals)
        if protected:
            scope = self.env.context.get('irg_guard_scope')
            if not (isinstance(scope, tuple) and len(scope) == 3
                    and scope[0] is _INTERNAL_TOKEN
                    and set(self.ids).issubset(scope[1])
                    and protected.issubset(scope[2])):
                raise AccessError(_('Los datos y vistos de la solicitud son inmutables. Cree una nueva solicitud.'))
        return super().write(vals)

    def copy(self, default=None):
        raise AccessError(_('Cree una nueva solicitud desde la matrícula para capturar sus datos actuales.'))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_academic_user()
        self.check_access_rights('create')
        if any(_TECHNICAL.intersection(vals) for vals in vals_list):
            raise AccessError(_('No puede establecer vistos, estado ni datos técnicos al crear la solicitud.'))
        # Defaults injected through RPC must not bypass the explicit-value gate.
        clean_context = {key: value for key, value in self.env.context.items()
                         if key != 'irg_guard_scope'
                         and not (key.startswith('default_') and key[8:] in _PROTECTED)}
        model = self.with_context(clean_context)
        prepared = []
        for incoming in vals_list:
            # Protected values require explicit request input or server capture.
            # Also fill technical fields so super.create cannot add ir.default
            # approvers/attachments after the guard has validated this request.
            vals = dict.fromkeys(_PROTECTED, False)
            vals.update(incoming)
            draft = model.new(vals)
            draft._guard_check_references()
            draft._guard_lock_targets()
            draft._guard_validate_request()
            snapshot = draft._guard_capture()
            enrollment, order = draft.student_course_id, draft.sale_order_id
            vals.update(
                origin_course_id=enrollment.course_id.id,
                origin_batch_id=enrollment.batch_id.id,
                origin_year_id=enrollment.academic_years_id.id,
                origin_payment_mode_id=order.payment_mode_id.id if order else False,
                origin_modality=draft._guard_origin_modality(),
                state='submitted', irg_guard_snapshot=snapshot,
                irg_guard_blocked=False,
            )
            prepared.append(vals)
        return super(EnrollmentChange, model).create(prepared)

    def _guard_read(self, records, phase=None):
        if not records:
            return records
        if len(records.exists()) != len(records):
            raise ValidationError(_('Uno de los registros de la solicitud ya no existe.'))
        # Finance has no general academic-model ACL in the base addon. Its
        # authorized private continuity check may read these references only;
        # record rules and the original company's whitelist still apply.
        academic_model = records._name in {
            'op.student.course', 'op.course', 'op.batch', 'op.academic.year'}
        original = records.with_env(self.env)
        if phase != 'finance' or not academic_model:
            original.check_access_rights('read')
        original.check_access_rule('read')
        records = original.sudo() if phase == 'finance' and academic_model else original
        if 'company_id' in records._fields:
            for record in records:
                if record.company_id and record.company_id not in self.env.companies:
                    raise AccessError(_('El registro pertenece a una compañía no autorizada.'))
        return records

    def _guard_check_references(self, phase=None):
        self.ensure_one()
        for records in (self.student_id, self.student_course_id,
                        self.dest_course_id, self.dest_batch_id, self.dest_year_id,
                        self.dest_payment_mode_id):
            self._guard_read(records, phase)
        if self.change_modality or self.change_payment:
            self._guard_read(self.sale_order_id)
            if self.change_modality:
                self._guard_read(self.sale_order_id.order_line)

    def _guard_lock_records(self, records):
        if not records:
            return
        records.flush_recordset()
        self.env.cr.execute(sql.SQL(
            'SELECT id FROM {} WHERE id IN %s ORDER BY id FOR UPDATE'
        ).format(sql.Identifier(records._table)), (tuple(sorted(records.ids)),))
        records.invalidate_recordset()

    def _guard_lock_request(self):
        self.ensure_one()
        self.check_access_rights('write')
        self.check_access_rule('write')
        self._guard_lock_records(self)

    def _guard_lock_targets(self, phase=None):
        # Always acquire enrollment before order, and order before its lines.
        enrollment = self._guard_read(self.student_course_id, phase)
        self._guard_lock_records(enrollment)
        self._guard_lock_records(self.student_id)
        self._guard_lock_records(self.student_id.partner_id)
        if self.change_course or self.change_batch:
            self._guard_lock_records(self._guard_read(enrollment.course_id | self.dest_course_id, phase))
            self._guard_lock_records(self._guard_read(enrollment.batch_id | self.dest_batch_id, phase))
        if self.change_year:
            self._guard_lock_records(self._guard_read(self.dest_year_id, phase))
        if self.change_payment or self.change_modality:
            fence_orders(self.env, self.sale_order_id.ids)
            self.sale_order_id.invalidate_recordset()
            if self.change_payment:
                self._guard_lock_records(self.dest_payment_mode_id)
            if self.change_modality:
                self._guard_lock_records(self.sale_order_id.order_line)

    def _guard_validate_request(self, phase=None):
        enrollment = self._guard_read(self.student_course_id, phase)
        if not self.student_id or not self.student_course_id:
            raise ValidationError(_('Seleccione alumno y matrícula.'))
        if enrollment.student_id != self.student_id:
            raise ValidationError(_('La matrícula no pertenece al alumno de la solicitud.'))
        if not any(self['change_' + name] for name in _FLAGS):
            raise ValidationError(_('Marque al menos un cambio de matrícula.'))
        for flag, destination in [('course', 'dest_course_id'), ('batch', 'dest_batch_id'),
                                  ('year', 'dest_year_id'), ('modality', 'dest_modality'),
                                  ('payment', 'dest_payment_mode_id')]:
            if self['change_' + flag] and not self[destination]:
                raise ValidationError(_('Falta un destino para el cambio solicitado: %s', flag))
        if self.change_course or self.change_batch:
            course = self.dest_course_id if self.change_course else enrollment.course_id
            batch = self._guard_read(self.dest_batch_id if self.change_batch else enrollment.batch_id, phase)
            if batch and batch.course_id != course:
                raise ValidationError(_('El lote no pertenece al curso correspondiente.'))
        if self.change_payment or self.change_modality:
            order = self.sale_order_id
            if not order:
                raise ValidationError(_('Seleccione el pedido para cambiar pago o modalidad.'))
            if 'student_id' in order._fields:
                if order._fields['student_id'].comodel_name != 'res.partner':
                    raise ValidationError(_('El vínculo de alumno del pedido no es compatible.'))
                partner = order.student_id or order.partner_id
            else:
                partner = order.partner_id
            if partner != self.student_id.partner_id:
                raise ValidationError(_('El pedido no pertenece al alumno de la solicitud.'))
        if self.change_modality:
            if 'x_studio_modalidad' not in self.env['sale.order.line']._fields:
                raise ValidationError(_('El pedido no tiene el campo de modalidad.'))
            if not self.sale_order_id.order_line:
                raise ValidationError(_('El pedido no tiene líneas de modalidad.'))

    def _guard_origin_modality(self):
        order = self.sale_order_id
        if order and 'x_studio_modalidad' in self.env['sale.order.line']._fields:
            self._guard_read(order)
            self._guard_read(order.order_line)
            return next((line.x_studio_modalidad for line in order.order_line
                         if line.x_studio_modalidad), False)
        return False

    def _guard_capture(self):
        enrollment = self.student_course_id
        academic = {'enrollment': {'student_id': self.student_id.id},
                    'student_partner_id': self.student_id.partner_id.id}
        if self.change_course or self.change_batch:
            academic['enrollment'].update(course_id=enrollment.course_id.id,
                                          batch_id=enrollment.batch_id.id)
        if self.change_year:
            academic['enrollment']['academic_years_id'] = enrollment.academic_years_id.id
        if self.change_payment or self.change_modality:
            order = self.sale_order_id
            academic['order'] = dict(id=order.id, partner_id=order.partner_id.id,
                                     company_id=order.company_id.id)
            if 'student_id' in order._fields:
                academic['order']['student_id'] = order.student_id.id
            if self.change_payment:
                academic['order']['payment_mode_id'] = order.payment_mode_id.id
            if self.change_modality:
                academic['lines'] = {str(line.id): line.x_studio_modalidad or False
                                     for line in order.order_line}
        return {'version': 1, 'academic': academic}

    def _guard_legacy(self, phase):
        # Historical requests prove only these persisted values. Never populate
        # an old origin from current records. Modality has no per-line evidence.
        if self.change_modality:
            raise GuardConflict(_('La solicitud anterior no conserva las líneas y modalidades originales.'))
        expected = {'enrollment': {'student_id': self.student_id.id}}
        for needed, key, origin, destination, changed in [
            (self.change_course or self.change_batch, 'course_id', self.origin_course_id,
             self.dest_course_id, self.change_course),
            (self.change_course or self.change_batch, 'batch_id', self.origin_batch_id,
             self.dest_batch_id, self.change_batch),
            (self.change_year, 'academic_years_id', self.origin_year_id,
             self.dest_year_id, self.change_year),
        ]:
            if needed:
                value = destination if phase == 'finance' and changed else origin
                if not value:
                    raise GuardConflict(_('La solicitud anterior no acredita el valor original de %s.', key))
                expected['enrollment'][key] = value.id
        if phase == 'finance' and not (self.academic_user_id and self.academic_date):
            raise GuardConflict(_('La solicitud anterior no acredita el visto académico.'))
        if self.change_payment:
            if not self.origin_payment_mode_id:
                raise GuardConflict(_('La solicitud anterior no acredita la forma de pago original.'))
            expected['order'] = {'id': self.sale_order_id.id,
                                 'payment_mode_id': self.origin_payment_mode_id.id}
        return expected

    def _guard_expected(self, phase):
        snapshot = self.irg_guard_snapshot
        if not snapshot:
            return self._guard_legacy(phase)
        if snapshot.get('version') != 1 or not snapshot.get('academic'):
            raise GuardConflict(_('La instantánea de la solicitud no es verificable.'))
        expected = dict(snapshot['academic'])
        expected['enrollment'] = dict(expected['enrollment'])
        if phase == 'finance':
            for flag, key, destination in [('course', 'course_id', self.dest_course_id),
                                           ('batch', 'batch_id', self.dest_batch_id),
                                           ('year', 'academic_years_id', self.dest_year_id)]:
                if self['change_' + flag]:
                    expected['enrollment'][key] = destination.id
            if self.change_modality:
                expected['lines'] = {line: self.dest_modality for line in expected['lines']}
        return expected

    def _guard_compare(self, phase):
        expected = self._guard_expected(phase)
        self._guard_validate_request(phase)
        enrollment = self._guard_read(self.student_course_id, phase)
        def compare(label, before, now):
            if before != now:
                if phase == 'finance' and label.startswith('Matrícula /'):
                    raise GuardConflict(_('Los datos académicos ya no coinciden con el visto aplicado.'))
                raise GuardConflict(_('%(field)s: se esperaba %(before)s y ahora es %(now)s.',
                                      field=label, before=before, now=now))
        for key, before in expected['enrollment'].items():
            compare('Matrícula / ' + key, before, enrollment[key].id)
        if 'student_partner_id' in expected:
            compare('Alumno / contacto', expected['student_partner_id'], self.student_id.partner_id.id)
        for key, before in expected.get('order', {}).items():
            now = self.sale_order_id.id if key == 'id' else self.sale_order_id[key].id
            compare('Pedido / ' + key, before, now)
        if 'lines' in expected:
            lines = {str(line.id): line.x_studio_modalidad or False for line in self.sale_order_id.order_line}
            compare('Líneas y modalidad', expected['lines'], lines)

    def _guard_block(self, detail):
        if not self.irg_guard_blocked:
            self._guard_internal({'irg_guard_blocked', 'irg_guard_conflict_detail'}).write({
                'irg_guard_blocked': True, 'irg_guard_conflict_detail': detail})
            self.message_post(body=html_escape(detail))
        return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'title': _('No se puede aprobar la solicitud'),
                           'message': _('%s Cree una nueva solicitud con los datos actuales. '
                                        'Esta solicitud se conserva como historial.',
                                        self.irg_guard_conflict_detail),
                           'type': 'warning', 'sticky': True}}

    def _guard_approve(self, phase):
        self.ensure_one()
        if phase == 'academic':
            self._check_academic_user()
        else:
            self._check_finance_user()
        self._guard_lock_request()
        if self.irg_guard_blocked:
            return self._guard_block(self.irg_guard_conflict_detail)
        # The parent still enforces its exact state/role contract. Compare only
        # pending requests, so stale done requests retain the original error.
        if (self.state != ('submitted' if phase == 'academic' else 'academic_approved')
                or (phase == 'finance' and not self.change_payment)):
            raise UserError(_('La solicitud no está pendiente de este visto.'))
        try:
            with self.env.cr.savepoint():
                self._guard_check_references(phase)
                self._guard_lock_targets(phase)
                self._guard_compare(phase)
                scoped = self._guard_internal(_TECHNICAL - {
                    'irg_guard_snapshot', 'irg_guard_blocked', 'irg_guard_conflict_detail',
                    'request_attachment_id', 'refuse_user_id'})
                parent = super(EnrollmentChange, scoped)
                return (parent.action_approve_academic() if phase == 'academic'
                        else parent.action_approve_finance())
        except (GuardConflict, ValidationError) as error:
            # Savepoint rolled back any partial parent changes first. Do not
            # raise after recording: the RPC must commit the permanent block.
            return self._guard_block(str(error))

    def action_approve_academic(self):
        return self._guard_approve('academic')

    def action_approve_finance(self):
        return self._guard_approve('finance')

    def action_refuse(self):
        self._guard_lock_request()
        scoped = self._guard_internal({'state', 'refuse_user_id'})
        return super(EnrollmentChange, scoped).action_refuse()

    def action_retry_pdf(self):
        self._guard_lock_request()
        scoped = self._guard_internal({'state', 'pdf_pending', 'final_attachment_id'})
        return super(EnrollmentChange, scoped).action_retry_pdf()

    def _generate_request_docx(self):
        scoped = self._guard_internal({'request_attachment_id'})
        return super(EnrollmentChange, scoped)._generate_request_docx()
