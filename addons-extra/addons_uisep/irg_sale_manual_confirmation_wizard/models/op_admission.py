# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def send_mail(self, force):
        """Override del routing del modulo selector existente.

        Cuando manual_wizard_enabled = True:
        - Si batch.code contiene 'ONL'  -> plantilla online (configurable)
        - En cualquier otro caso       -> plantilla por defecto (configurable)
        - Si las plantillas no estan configuradas, cae a las xmlids historicas.

        Cuando manual_wizard_enabled = False: delega 100% en super().
        """
        ad = self.env['auto.admission.required'].search([], limit=1)
        if not ad or not ad.manual_wizard_enabled:
            return super().send_mail(force)

        if self.email_send_ok:
            return  # super delega aqui

        if not self.tutor_id and self.batch_id:
            tutor = False
            if ad:
                tutor = ad.br_tutor_id if self.course_id.lang == 'pt_BR' else ad.mx_tutor_id
            if not tutor:
                tutor = self.env.user
            if tutor:
                _logger.info("IRG Manual Wizard: auto-asignando tutor %s al lote %s para admisión %s", tutor.name, self.batch_id.name, self.name)
                self.batch_id.write({'tutor_id': tutor.id})

        student_name = self.name
        if not self.tutor_id:
            raise UserError(_('%s - El aplicante necesita un Tutor asignado.') % student_name)
        if not self.batch_id:
            raise UserError(_('%s - Necesita asignar un grupo.') % student_name)
        if not self.batch_id.start_date:
            raise UserError(_('%s - Necesita establecer fecha de inicio de Clases.') % student_name)

        batch_code = (self.batch_id.code or '').upper()
        is_online_batch = 'ONL' in batch_code

        template = False
        if is_online_batch:
            template = ad.welcome_template_online_id or self.env.ref(
                'irg_elearning_correo_bienvenida_selector.email_op_admission_confirm_online',
                raise_if_not_found=False,
            )
        if not template:
            template = ad.welcome_template_default_id or self.env.ref(
                'isep_elearning_custom.email_op_admission_confirm',
                raise_if_not_found=False,
            )
        if not template:
            _logger.warning("IRG Manual Wizard: ninguna plantilla resuelta, delegando en super()")
            return super().send_mail(force)

        _logger.info(
            "IRG Manual Wizard: enviando bienvenida admission=%s batch=%s online=%s template=%s",
            self.id, batch_code, is_online_batch, template.name,
        )

        if hasattr(self, '_fix_welcome_password_placeholder'):
            self._fix_welcome_password_placeholder(template)
        if hasattr(self, '_welcome_password_context'):
            welcome_ctx = self._welcome_password_context()
        else:
            welcome_ctx = {}

        self.with_context(
            force_send=force,
            **welcome_ctx,
        ).message_post_with_template(template.id, email_layout_xmlid=False)
        self.email_send_ok = True

    def submit_form(self):
        # Aseguramos que se guarde la fecha de nacimiento o un default
        birth = self.birth_date or '2000-01-01'
        res = super().submit_form()
        for record in self:
            if record.partner_id and not record.partner_id.birth_date:
                record.partner_id.write({'birth_date': birth})
        return res

    def enroll_student(self):
        for record in self:
            if record.partner_id and not record.partner_id.birth_date:
                record.partner_id.write({'birth_date': record.birth_date or '2000-01-01'})
        
        # Guardar fechas de admisión originales para evitar que el super() las pise con la fecha de hoy
        saved_dates = {r.id: r.admission_date for r in self}
        
        res = super().enroll_student()
        
        for record in self:
            orig_date = saved_dates.get(record.id)
            if orig_date and record.admission_date != orig_date:
                _logger.info(
                    "IRG Manual Wizard: Restaurando admission_date a %s para la admisión %s (evitando sobreescritura de enroll_student)",
                    orig_date, record.name
                )
                record.admission_date = orig_date
        return res

    def get_student_vals(self):
        res = super().get_student_vals()
        if res and not res.get('birth_date'):
            res['birth_date'] = self.birth_date or self.partner_id.birth_date or '2000-01-01'
        return res

