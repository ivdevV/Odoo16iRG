# -*- coding: utf-8 -*-

import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html_escape

_logger = logging.getLogger(__name__)

MODALITY_SELECTION = [
    ('Online', 'Online'),
    ('Presencial', 'Presencial'),
    ('Homeclass', 'Homeclass'),
]


class IrgEnrollmentChange(models.Model):
    _name = 'irg.enrollment.change'
    _description = 'Solicitud de modificación de matrícula'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        default='New',
        tracking=True,
    )
    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    student_course_id = fields.Many2one(
        'op.student.course',
        string='Matrícula de origen',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de venta',
        ondelete='restrict',
        tracking=True,
    )
    state = fields.Selection(
        [
            ('submitted', 'Enviada'),
            ('academic_approved', 'Pendiente de finanzas'),
            ('done', 'Hecha'),
            ('refused', 'Denegada'),
        ],
        string='Estado',
        default='submitted',
        required=True,
        tracking=True,
    )
    change_course = fields.Boolean(string='Cambio de curso')
    change_batch = fields.Boolean(string='Cambio de lote')
    change_modality = fields.Boolean(string='Cambio de modalidad')
    change_year = fields.Boolean(string='Cambio de año académico')
    change_payment = fields.Boolean(string='Cambio de forma de pago')
    origin_course_id = fields.Many2one('op.course', string='Curso de origen')
    dest_course_id = fields.Many2one('op.course', string='Curso de destino')
    origin_batch_id = fields.Many2one('op.batch', string='Lote de origen')
    dest_batch_id = fields.Many2one('op.batch', string='Lote de destino')
    origin_modality = fields.Selection(MODALITY_SELECTION, string='Modalidad de origen')
    dest_modality = fields.Selection(MODALITY_SELECTION, string='Modalidad de destino')
    origin_year_id = fields.Many2one('op.academic.year', string='Año de origen')
    dest_year_id = fields.Many2one('op.academic.year', string='Año de destino')
    origin_payment_mode_id = fields.Many2one(
        'account.payment.mode',
        string='Forma de pago de origen',
    )
    dest_payment_mode_id = fields.Many2one(
        'account.payment.mode',
        string='Forma de pago de destino',
    )
    academic_user_id = fields.Many2one('res.users', string='Visto académico por', readonly=True)
    academic_date = fields.Datetime(string='Fecha visto académico', readonly=True)
    finance_user_id = fields.Many2one('res.users', string='Visto financiero por', readonly=True)
    finance_date = fields.Datetime(string='Fecha visto financiero', readonly=True)
    refuse_user_id = fields.Many2one('res.users', string='Denegada por', readonly=True)
    request_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Solicitud Word',
        readonly=True,
        copy=False,
    )
    final_attachment_id = fields.Many2one(
        'ir.attachment',
        string='PDF final',
        readonly=True,
        copy=False,
    )
    pdf_pending = fields.Boolean(string='PDF pendiente', default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'irg.enrollment.change'
                ) or 'New'
        return super().create(vals_list)

    def _is_academic_user(self):
        user = self.env.user
        return user.has_group('irg_enrollment_modification.group_academic') or user.has_group(
            'base.group_system'
        )

    def _is_finance_user(self):
        user = self.env.user
        return user.has_group('account.group_account_invoice') or user.has_group(
            'base.group_system'
        )

    def _check_academic_user(self):
        if not self._is_academic_user():
            raise AccessError(
                _('No tiene permisos del departamento académico para esta acción.')
            )

    def _check_finance_user(self):
        if not self._is_finance_user():
            raise AccessError(
                _('No tiene permisos de contabilidad para esta acción.')
            )

    def action_approve_academic(self):
        self.ensure_one()
        self._check_academic_user()
        if self.state != 'submitted':
            raise UserError(_('Solo se puede dar el visto académico a una solicitud enviada.'))
        self._write_academic_fields()
        self.write({
            'academic_user_id': self.env.uid,
            'academic_date': fields.Datetime.now(),
        })
        self._post_student(_(
            'Visto académico de la solicitud %(name)s aplicado por %(operator)s.',
            name=html_escape(self.name),
            operator=html_escape(self.env.user.name),
        ))
        if self.change_payment:
            self.write({'state': 'academic_approved'})
            self.message_post(body=_('Pendiente de visto del área financiera.'))
            return True
        return self._close_with_pdf()

    def action_approve_finance(self):
        self.ensure_one()
        self._check_finance_user()
        if self.state != 'academic_approved' or not self.change_payment:
            raise UserError(
                _('Solo se puede dar el visto financiero a una solicitud pendiente de pago.')
            )
        self._write_payment_mode()
        self.write({
            'finance_user_id': self.env.uid,
            'finance_date': fields.Datetime.now(),
        })
        self._post_student(_(
            'Visto financiero de la solicitud %(name)s aplicado por %(operator)s.',
            name=html_escape(self.name),
            operator=html_escape(self.env.user.name),
        ))
        return self._close_with_pdf()

    def action_refuse(self):
        self.ensure_one()
        if self.state == 'submitted':
            self._check_academic_user()
            self.write({
                'state': 'refused',
                'refuse_user_id': self.env.uid,
            })
            body = _(
                'Solicitud %(name)s denegada por %(operator)s. '
                'No se ha modificado la matrícula ni la forma de pago.',
                name=html_escape(self.name),
                operator=html_escape(self.env.user.name),
            )
            self._post_student(body)
            self.message_post(body=body)
            return True
        if self.state == 'academic_approved':
            self._check_finance_user()
            self.write({
                'state': 'refused',
                'refuse_user_id': self.env.uid,
            })
            body = _(
                'El cambio académico de la solicitud %(name)s queda aplicado. '
                'El cambio de forma de pago ha sido denegado por %(operator)s.',
                name=html_escape(self.name),
                operator=html_escape(self.env.user.name),
            )
            self._post_student(body)
            self.message_post(body=body)
            return True
        raise UserError(_('Esta solicitud no se puede denegar en su estado actual.'))

    def action_retry_pdf(self):
        self.ensure_one()
        if not self.pdf_pending or self.state != 'done':
            raise UserError(_('No hay un PDF pendiente de generar para esta solicitud.'))
        if self.change_payment:
            self._check_finance_user()
        else:
            self._check_academic_user()
        return self._close_with_pdf()

    def _write_academic_fields(self):
        self.ensure_one()
        vals = {}
        if self.change_course:
            if not self.dest_course_id:
                raise ValidationError(_('Falta el curso de destino.'))
            vals['course_id'] = self.dest_course_id.id
        if self.change_batch:
            if not self.dest_batch_id:
                raise ValidationError(_('Falta el lote de destino.'))
            vals['batch_id'] = self.dest_batch_id.id
        if self.change_year:
            if not self.dest_year_id:
                raise ValidationError(_('Falta el año académico de destino.'))
            vals['academic_years_id'] = self.dest_year_id.id
        if vals:
            self.student_course_id.sudo().write(vals)
        if self.change_modality:
            self._write_modality()

    def _write_modality(self):
        self.ensure_one()
        if not self.dest_modality:
            raise ValidationError(_('Falta la modalidad de destino.'))
        if not self.sale_order_id:
            raise ValidationError(
                _('Seleccione el pedido de venta para cambiar la modalidad.')
            )
        lines = self.sale_order_id.sudo().order_line
        if 'x_studio_modalidad' not in lines._fields:
            raise ValidationError(
                _('El pedido no tiene el campo de modalidad. No se puede aplicar el cambio.')
            )
        if not lines:
            raise ValidationError(
                _('El pedido vinculado no tiene líneas donde escribir la modalidad.')
            )
        lines.write({'x_studio_modalidad': self.dest_modality})

    def _write_payment_mode(self):
        self.ensure_one()
        if not self.sale_order_id or not self.dest_payment_mode_id:
            raise ValidationError(_('Faltan el pedido o la forma de pago de destino.'))
        self.sale_order_id.sudo().write({
            'payment_mode_id': self.dest_payment_mode_id.id,
        })

    def _generate_request_docx(self):
        self.ensure_one()
        docx_bytes = self.env['irg.enrollment.change.document'].build_docx_bytes(
            self, stage='request',
        )
        attachment = self.env['ir.attachment'].create({
            'name': 'solicitud.docx',
            'type': 'binary',
            'datas': base64.b64encode(docx_bytes),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': (
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ),
        })
        self.write({'request_attachment_id': attachment.id})
        self._post_student(
            _(
                'Solicitud de modificación de matrícula %(name)s creada por %(operator)s.',
                name=html_escape(self.name),
                operator=html_escape(self.env.user.name),
            ),
            attachment_ids=[attachment.id],
        )
        self.message_post(
            body=_('Se ha generado la solicitud en Word.'),
            attachment_ids=[attachment.id],
        )
        return attachment

    def _close_with_pdf(self):
        self.ensure_one()
        try:
            pdf_bytes = self.env['irg.enrollment.change.document'].build_pdf_bytes(self)
        except UserError as err:
            _logger.warning('Enrollment change PDF failed for %s: %s', self.name, err)
            self.write({
                'state': 'done',
                'pdf_pending': True,
            })
            body = _(
                'La solicitud %(name)s está cerrada, pero no se pudo generar el PDF: %(error)s',
                name=html_escape(self.name),
                error=html_escape(str(err)),
            )
            self._post_student(body)
            self.message_post(body=body)
            return True
        attachment = self.env['ir.attachment'].create({
            'name': 'final.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_bytes),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        self.write({
            'state': 'done',
            'pdf_pending': False,
            'final_attachment_id': attachment.id,
        })
        self._post_student(
            _(
                'PDF final de la solicitud %(name)s.',
                name=html_escape(self.name),
            ),
            attachment_ids=[attachment.id],
        )
        self.message_post(
            body=_('Se ha generado el PDF final.'),
            attachment_ids=[attachment.id],
        )
        return True

    def _post_student(self, body, attachment_ids=None):
        self.student_id.sudo().message_post(
            body=body,
            author_id=self.env.user.partner_id.id,
            attachment_ids=attachment_ids or [],
        )
