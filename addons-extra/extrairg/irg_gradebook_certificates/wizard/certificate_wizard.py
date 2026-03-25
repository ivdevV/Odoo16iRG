# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..models.irg_certificate_request import (
    CERTIFICATE_TYPES,
    SHIPPING_TYPES,
    CUSTOM_OPTIONS,
    PRICE_MAP,
    SHIPPING_MAP,
    PHYSICAL_TYPES,
    SIGNER_SELECTION,
)


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
    certificate_type = fields.Selection(
        selection=CERTIFICATE_TYPES,
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

    def action_generate(self):
        """Create the certificate, generate the PDF and return a download action."""
        self.ensure_one()
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook_student_id.id,
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
