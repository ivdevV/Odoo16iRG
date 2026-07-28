# -*- coding: utf-8 -*-
import base64
import uuid
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource

_logger = logging.getLogger(__name__)


class PracticeAgreement(models.Model):
    _name = 'practice.agreement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Convenio Marco de Prácticas'
    _order = 'id desc'

    name = fields.Char(
        string='Referencia Convenio',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo')
    )
    practice_center_id = fields.Many2one(
        'practice.center',
        string='Centro de Prácticas',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Contacto Partner',
        related='practice_center_id.partner_id',
        store=True,
        readonly=True
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Enviado a Firma'),
        ('completed', 'Firmado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True, index=True)

    # Datos iRG (Lugar y fecha de firma)
    city_signature = fields.Char(string='Lugar de Firma iRG', default='Barcelona')
    date_signature = fields.Date(string='Fecha de Firma', default=fields.Date.context_today)

    # Datos del Centro Colaborador (Rellenables en Backend o Formulario Web)
    center_official_name = fields.Char(string='Nombre Oficial / Razón Social Centro', tracking=True)
    center_vat = fields.Char(string='NIF / CIF Centro', tracking=True)
    signatory_name = fields.Char(string='Nombre Representante Legal', tracking=True)
    signatory_title = fields.Char(string='Cargo Representante Legal', default='Representante Legal', tracking=True)
    street = fields.Char(string='Dirección Sede')
    city = fields.Char(string='Ciudad')
    zip = fields.Char(string='Código Postal')
    state_id = fields.Many2one('res.country.state', string='Provincia / Estado')
    country_id = fields.Many2one('res.country', string='País')
    phone = fields.Char(string='Teléfono Contacto')
    email = fields.Char(string='Email de Envío', tracking=True)

    # Seguridad y Firma Digital
    access_token = fields.Char(string='Token de Acceso Seguro', copy=False, index=True)
    signed_on = fields.Datetime(string='Fecha y Hora de Firma Digital', readonly=True, copy=False)
    signed_by = fields.Char(string='Firmado Por (Nombre)', readonly=True, copy=False)
    signed_ip = fields.Char(string='IP del Firmante', readonly=True, copy=False)
    signature_center = fields.Binary(string='Firma Centro Colaborador', copy=False, attachment=True)
    signature_irg = fields.Binary(
        string='Firma Oficial iRG',
        default=lambda self: self._default_signature_irg(),
        attachment=True
    )

    pdf_attachment_id = fields.Many2one('ir.attachment', string='PDF Convenio Firmado', copy=False, readonly=True)

    @api.model
    def _default_signature_irg(self):
        """Carga por defecto la firma PNG del Sr. Raimon Gaja situada en assets."""
        path = get_module_resource('irg_practice_agreement_sign', 'static/src/img', 'firma_raimon.png')
        if path:
            try:
                with open(path, 'rb') as f:
                    return base64.b64encode(f.read())
            except Exception as e:
                _logger.warning("No se pudo cargar la firma por defecto de Raimon Gaja: %s", e)
        return False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('practice.agreement') or _('Nuevo')
            if not vals.get('access_token'):
                vals['access_token'] = str(uuid.uuid4())
            # Sincronizar datos por defecto del centro si viene practice_center_id
            if vals.get('practice_center_id') and not vals.get('center_official_name'):
                center = self.env['practice.center'].browse(vals['practice_center_id'])
                vals.update({
                    'center_official_name': center.official_name or center.name,
                    'signatory_name': center.signatory_name or center.coordinator,
                    'street': center.street,
                    'city': center.city,
                    'zip': center.postal_code,
                    'state_id': center.state_id.id if center.state_id else False,
                    'country_id': center.country_id.id if center.country_id else False,
                    'phone': center.phone or center.mobil,
                    'email': center.email,
                    'center_vat': center.partner_id.vat if center.partner_id else False,
                })
        return super(PracticeAgreement, self).create(vals_list)

    def action_ensure_token(self):
        """Asegura que exista un access_token para compartir el enlace."""
        for record in self:
            if not record.access_token:
                record.access_token = str(uuid.uuid4())
        return True

    def get_portal_url(self):
        """Devuelve el enlace público único para firma."""
        self.ensure_one()
        self.action_ensure_token()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/convenio/firma/{self.access_token}"

    def action_send_by_email(self):
        """Genera el token y envía el correo electrónico con el enlace de firma."""
        self.ensure_one()
        self.action_ensure_token()
        if not self.email:
            raise UserError(_("Debe especificar un email de envío antes de enviar el convenio."))

        template = self.env.ref('irg_practice_agreement_sign.email_template_practice_agreement_sign', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        self.write({'state': 'sent'})
        return True

    def action_complete_signature(self, signature_base64, signer_name, ip_address=False):
        """Procesa la firma del centro, genera el PDF definitivo y lo adjunta."""
        self.ensure_one()
        if not signature_base64:
            raise UserError(_("Debe proporcionar la imagen de la firma."))

        now = fields.Datetime.now()
        # Formatear base64 si incluye cabecera data:image/png;base64,
        if isinstance(signature_base64, str) and ',' in signature_base64:
            signature_base64 = signature_base64.split(',')[1]

        self.write({
            'signature_center': signature_base64,
            'signed_by': signer_name or self.signatory_name,
            'signed_on': now,
            'signed_ip': ip_address or '0.0.0.0',
            'state': 'completed',
        })

        # Generar el PDF oficial del Convenio
        pdf_content, report_format = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'irg_practice_agreement_sign.action_report_practice_agreement',
            [self.id]
        )

        filename = f"Convenio_Marco_{self.center_official_name or self.practice_center_id.name}_{self.id}.pdf"
        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': base64.b64encode(pdf_content),
            'res_model': 'practice.agreement',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        self.write({'pdf_attachment_id': attachment.id})

        # Copiar adjunto al módulo irg_practice_center_documents si aplica
        if hasattr(self.practice_center_id, 'document_ids'):
            self.env['ir.attachment'].sudo().create({
                'name': f"Convenio Firmado - {filename}",
                'datas': base64.b64encode(pdf_content),
                'res_model': 'practice.center',
                'res_id': self.practice_center_id.id,
                'mimetype': 'application/pdf',
            })

        # Enviar email de notificación de convenio firmado a ambas partes
        body_msg = _("El convenio de colaboración ha sido firmado digitalmente por %s el %s.") % (signer_name, str(now))
        self.message_post(
            body=body_msg,
            attachment_ids=[attachment.id]
        )
        return True

    def action_view_pdf(self):
        """Permite visualizar/descargar el PDF del convenio desde el formulario backend."""
        self.ensure_one()
        return self.env.ref('irg_practice_agreement_sign.action_report_practice_agreement').report_action(self)
