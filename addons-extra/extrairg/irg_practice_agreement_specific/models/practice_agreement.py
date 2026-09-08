# -*- coding: utf-8 -*-
import base64
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError

ESPECIFICO_TYPES = ('especifico_internacional', 'especifico_nacional')


class PracticeAgreement(models.Model):
    _inherit = 'practice.agreement'

    agreement_type = fields.Selection(
        selection_add=[
            ('especifico_internacional', 'Convenio Específico Internacional'),
            ('especifico_nacional', 'Convenio Específico Nacional'),
        ],
        ondelete={
            'especifico_internacional': 'set default',
            'especifico_nacional': 'set default',
        },
    )
    practice_request_id = fields.Many2one(
        'practice.request',
        string='Solicitud de prácticas',
        ondelete='set null',
        index=True,
        copy=False,
    )
    student_name = fields.Char(string='Nombre del estudiante')
    student_email = fields.Char(string='Email del estudiante')
    student_vat = fields.Char(string='Documento del estudiante')
    course_name = fields.Char(string='Máster / curso')
    start_date = fields.Date(string='Fecha de inicio de prácticas')
    final_date = fields.Date(string='Fecha de fin de prácticas')
    total_hours = fields.Float(string='Horas totales')
    practice_days = fields.Char(string='Días de prácticas')
    schedule_hours = fields.Char(string='Horario')
    modality = fields.Char(string='Modalidad')
    tutor_name = fields.Char(string='Tutor')
    tutor_vat = fields.Char(string='Documento del tutor')
    student_proposed_activities = fields.Text(
        string='Actividades propuestas por el alumno',
    )
    student_access_token = fields.Char(
        string='Token de firma del estudiante',
        copy=False,
        index=True,
    )
    signature_student = fields.Binary(
        string='Firma del estudiante',
        copy=False,
        attachment=True,
    )
    signed_by_student = fields.Char(
        string='Firmado por (estudiante)',
        readonly=True,
        copy=False,
    )
    signed_on_student = fields.Datetime(
        string='Fecha de firma del estudiante',
        readonly=True,
        copy=False,
    )
    signed_ip_student = fields.Char(
        string='IP del estudiante',
        readonly=True,
        copy=False,
    )

    def _is_especifico(self):
        self.ensure_one()
        return self.agreement_type in ESPECIFICO_TYPES

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('agreement_type') in ESPECIFICO_TYPES and not vals.get(
                'student_access_token'
            ):
                vals['student_access_token'] = str(uuid.uuid4())
        return super().create(vals_list)

    def action_ensure_student_token(self):
        for record in self:
            if record._is_especifico() and not record.student_access_token:
                record.student_access_token = str(uuid.uuid4())
        return True

    def get_student_portal_url(self):
        self.ensure_one()
        self.action_ensure_student_token()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return '%s/convenio/firma-alumno/%s' % (base_url, self.student_access_token)

    def action_send_by_email(self):
        self.ensure_one()
        if not self._is_especifico():
            return super().action_send_by_email()
        self.action_ensure_token()
        self.action_ensure_student_token()
        if not self.email:
            raise UserError(
                _('Debe especificar un email del centro antes de enviar el convenio.')
            )
        if not self.student_email:
            raise UserError(
                _('Debe especificar un email del estudiante antes de enviar el convenio.')
            )
        center_template = self.env.ref(
            'irg_practice_agreement_specific.email_template_especifico_center',
            raise_if_not_found=False,
        )
        student_template = self.env.ref(
            'irg_practice_agreement_specific.email_template_especifico_student',
            raise_if_not_found=False,
        )
        if center_template:
            center_template.send_mail(self.id, force_send=True)
        if student_template:
            student_template.send_mail(self.id, force_send=True)
        self.write({'state': 'sent'})
        return True

    def _normalize_signature(self, signature_base64):
        if isinstance(signature_base64, str) and ',' in signature_base64:
            return signature_base64.split(',')[1]
        return signature_base64

    def _store_center_signature_and_maybe_finalize(
        self, signature_base64, signer_name, ip_address=False
    ):
        self.ensure_one()
        if not signature_base64:
            raise UserError(_('Debe proporcionar la imagen de la firma.'))
        if self.state == 'completed':
            return True
        now = fields.Datetime.now()
        self.write({
            'signature_center': self._normalize_signature(signature_base64),
            'signed_by': signer_name or self.signatory_name,
            'signed_on': now,
            'signed_ip': ip_address or '0.0.0.0',
        })
        if self.signature_student:
            self._finalize_especifico_pdf()
        return True

    def action_complete_signature(self, signature_base64, signer_name, ip_address=False):
        self.ensure_one()
        if not self._is_especifico():
            return super().action_complete_signature(
                signature_base64, signer_name, ip_address
            )
        return self._store_center_signature_and_maybe_finalize(
            signature_base64, signer_name, ip_address
        )

    def action_complete_student_signature(
        self, signature_base64, signer_name, ip_address=False
    ):
        self.ensure_one()
        if not self._is_especifico():
            raise UserError(
                _('Solo los convenios específicos admiten la firma del estudiante.')
            )
        if not signature_base64:
            raise UserError(_('Debe proporcionar la imagen de la firma.'))
        if self.state == 'completed':
            return True
        now = fields.Datetime.now()
        self.write({
            'signature_student': self._normalize_signature(signature_base64),
            'signed_by_student': signer_name or self.student_name,
            'signed_on_student': now,
            'signed_ip_student': ip_address or '0.0.0.0',
        })
        if self.signature_center:
            self._finalize_especifico_pdf()
        return True

    def _especifico_pdf_filename(self):
        self.ensure_one()
        slug = (
            'Nacional'
            if self.agreement_type == 'especifico_nacional'
            else 'Internacional'
        )
        student = self.student_name or 'Alumno'
        center = self.center_official_name or self.practice_center_id.name or 'Centro'
        return 'Convenio_Especifico_%s_%s_%s_%s.pdf' % (
            slug, student, center, self.id
        )

    def _finalize_especifico_pdf(self):
        self.ensure_one()
        self.write({'state': 'completed'})
        pdf_content, _report_format = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'irg_practice_agreement_sign.action_report_practice_agreement',
            [self.id],
        )
        filename = self._especifico_pdf_filename()
        pdf_b64 = base64.b64encode(pdf_content)
        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': pdf_b64,
            'res_model': 'practice.agreement',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        self.write({'pdf_attachment_id': attachment.id})
        if self.practice_center_id:
            self.env['ir.attachment'].sudo().create({
                'name': 'Convenio Firmado - %s' % filename,
                'datas': pdf_b64,
                'res_model': 'practice.center',
                'res_id': self.practice_center_id.id,
                'mimetype': 'application/pdf',
            })
        if self.practice_request_id:
            self.env['ir.attachment'].sudo().create({
                'name': filename,
                'datas': pdf_b64,
                'res_model': 'practice.request',
                'res_id': self.practice_request_id.id,
                'mimetype': 'application/pdf',
            })
        self.message_post(
            body=_(
                'El convenio específico ha sido firmado por el estudiante y el centro.'
            ),
            attachment_ids=[attachment.id],
        )
        return True
