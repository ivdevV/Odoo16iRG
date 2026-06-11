# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..models.irg_certificate_request import (
    SHIPPING_TYPES,
    CUSTOM_OPTIONS,
    PRICE_MAP,
    SHIPPING_MAP,
    PHYSICAL_TYPES,
    SIGNER_SELECTION,
)


WIZARD_DOCUMENT_TYPES = [
    ('gradebook', 'Certificado de Notas Completo'),
    ('gradebook_partial', 'Certificado de Notas Parcial'),
]

WIZARD_CERTIFICATE_TYPES = [
    ('digital', 'Digital'),
    ('physical', 'Físico'),
    ('custom', 'A Medida'),
    ('physical_apostilled', 'Físico Apostillado'),
]


class IrgCertificateWizard(models.TransientModel):
    _name = 'irg.certificate.wizard'
    _description = 'Asistente de Generación de Certificado de Notas'

    def _default_gradebook(self):
        return self.env.context.get('active_id')

    gradebook_student_id = fields.Many2one(
        'app.gradebook.student',
        string='Libreta',
        default=_default_gradebook,
        required=True,
        readonly=True,
    )
    partner_name = fields.Char(
        string='Alumno',
        related='gradebook_student_id.partner_id.name',
        readonly=True,
    )
    course_name = fields.Char(
        string='Programa',
        related='gradebook_student_id.course_id.name',
        readonly=True,
    )
    document_type = fields.Selection(
        selection=WIZARD_DOCUMENT_TYPES,
        string='Tipo de Documento',
        default='gradebook',
        required=True,
    )
    certificate_type = fields.Selection(
        selection=WIZARD_CERTIFICATE_TYPES,
        string='Tipo de Certificado',
        required=True,
        default='digital',
    )
    shipping_type = fields.Selection(
        selection=SHIPPING_TYPES,
        string='Tipo de Envío',
    )
    custom_description = fields.Text(
        string='Descripción de Peticiones',
    )
    custom_options = fields.Selection(
        selection=CUSTOM_OPTIONS,
        string='Opción Adicional',
    )
    signer = fields.Selection(
        selection=SIGNER_SELECTION,
        string='Persona que Firma',
        default='raimon',
    )
    price_total = fields.Float(
        string='Total (€)',
        compute='_compute_price',
        digits=(6, 2),
    )

    @api.depends('certificate_type', 'shipping_type')
    def _compute_price(self):
        for rec in self:
            base = PRICE_MAP.get(rec.certificate_type, 0.0)
            shipping = (
                SHIPPING_MAP.get(rec.shipping_type, 0.0)
                if rec.certificate_type in PHYSICAL_TYPES
                else 0.0
            )
            rec.price_total = base + shipping

    @api.constrains('certificate_type', 'shipping_type')
    def _check_shipping(self):
        for rec in self:
            if rec.certificate_type in PHYSICAL_TYPES and not rec.shipping_type:
                raise ValidationError(
                    _('El tipo de envío es obligatorio para certificados físicos.')
                )

    @api.constrains('document_type', 'gradebook_student_id')
    def _check_gradebook_state(self):
        for rec in self:
            if rec.document_type == 'gradebook' and rec.gradebook_student_id.state != 'done':
                raise ValidationError(
                    _("Para solicitar un Certificado de Notas Completo, la libreta académica debe estar finalizada (estado 'Finalizado').")
                )

    def action_generate(self):
        """Create the certificate, generate the PDF and return a download action."""
        self.ensure_one()
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook_student_id.id,
            'document_type': self.document_type,
            'certificate_type': self.certificate_type,
            'shipping_type': self.shipping_type or False,
            'custom_description': self.custom_description or False,
            'custom_options': self.custom_options or False,
            'signer': self.signer,
            'state': 'done',
            'origin': 'backend',
        })
        cert._generate_and_attach_pdf()
        return cert.action_download_pdf()
