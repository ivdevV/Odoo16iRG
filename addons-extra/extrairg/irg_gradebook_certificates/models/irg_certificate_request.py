# -*- coding: utf-8 -*-
import base64
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CERTIFICATE_TYPES = [
    ('digital', 'Certificado de Notas Digital'),
    ('physical', 'Certificado de Notas Físico'),
    ('custom', 'Certificado de Notas a Medida'),
    ('physical_apostilled', 'Certificado de Notas Físico Apostillado'),
]

SHIPPING_TYPES = [
    ('national', 'Envío Nacional'),
    ('international', 'Envío Internacional'),
]

STATE_SELECTION = [
    ('draft', 'Borrador'),
    ('pending_payment', 'Pendiente de Pago'),
    ('paid', 'Pagado'),
    ('in_process', 'En Proceso'),
    ('sent', 'Enviado'),
    ('done', 'Finalizado'),
    ('cancelled', 'Cancelado'),
]

CUSTOM_OPTIONS = [
    ('language_en', 'En Inglés'),
    ('language_fr', 'En Francés'),
    ('specific_subjects', 'Asignaturas Específicas'),
    ('official_seal', 'Con Sello Oficial'),
]

PRICE_MAP = {
    'digital': 30.0,
    'physical': 40.0,
    'custom': 40.0,
    'physical_apostilled': 80.0,
}

SHIPPING_MAP = {
    'national': 20.0,
    'international': 60.0,
}

PHYSICAL_TYPES = ('physical', 'physical_apostilled')


class IrgCertificateRequest(models.Model):
    _name = 'irg.certificate.request'
    _description = 'Solicitud de Certificado de Notas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    name = fields.Char(
        string='Referencia',
        readonly=True,
        copy=False,
        default='New',
    )
    origin = fields.Selection(
        [('backend', 'Generación Interna'), ('portal', 'Solicitud Portal')],
        string='Origen',
        default='backend',
        readonly=True,
        required=True,
    )

    # ------------------------------------------------------------------
    # Academic data (from gradebook)
    # ------------------------------------------------------------------

    gradebook_student_id = fields.Many2one(
        'app.gradebook.student',
        string='Libreta',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Alumno',
        related='gradebook_student_id.partner_id',
        store=True,
    )
    admission_id = fields.Many2one(
        'op.admission',
        string='Admisión',
        related='gradebook_student_id.admission_id',
        store=True,
    )
    course_id = fields.Many2one(
        'op.course',
        string='Programa',
        related='gradebook_student_id.course_id',
        store=True,
    )
    batch_id = fields.Many2one(
        'op.batch',
        string='Grupo',
        related='gradebook_student_id.batch_id',
        store=True,
    )

    # ------------------------------------------------------------------
    # Certificate options
    # ------------------------------------------------------------------

    certificate_type = fields.Selection(
        selection=CERTIFICATE_TYPES,
        string='Tipo de Certificado',
        required=True,
        tracking=True,
    )
    shipping_type = fields.Selection(
        selection=SHIPPING_TYPES,
        string='Tipo de Envío',
        tracking=True,
    )
    custom_description = fields.Text(
        string='Descripción de Peticiones',
    )
    custom_options = fields.Selection(
        selection=CUSTOM_OPTIONS,
        string='Opción Adicional',
    )

    # ------------------------------------------------------------------
    # State / lifecycle
    # ------------------------------------------------------------------

    state = fields.Selection(
        selection=STATE_SELECTION,
        string='Estado',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )
    request_date = fields.Datetime(
        string='Fecha de Solicitud',
        default=fields.Datetime.now,
        readonly=True,
        copy=False,
    )
    delivery_date = fields.Datetime(
        string='Fecha de Entrega/Envío',
        copy=False,
        tracking=True,
    )
    tracking_number = fields.Char(
        string='Número de Seguimiento',
        copy=False,
        tracking=True,
    )
    apostille_done = fields.Boolean(
        string='Apostillado Tramitado',
        default=False,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------

    price_base = fields.Float(
        string='Precio Base (€)',
        compute='_compute_prices',
        store=True,
        digits=(6, 2),
    )
    price_shipping = fields.Float(
        string='Precio Envío (€)',
        compute='_compute_prices',
        store=True,
        digits=(6, 2),
    )
    price_total = fields.Float(
        string='Total (€)',
        compute='_compute_prices',
        store=True,
        digits=(6, 2),
    )

    # ------------------------------------------------------------------
    # Linked records
    # ------------------------------------------------------------------

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de Venta',
        copy=False,
        readonly=True,
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='PDF Generado',
        copy=False,
        readonly=True,
    )
    internal_notes = fields.Text(
        string='Notas Internas',
    )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = (
                self.env['ir.sequence'].next_by_code('irg.certificate.request') or 'New'
            )
        return super().create(vals)

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------

    @api.depends('certificate_type', 'shipping_type')
    def _compute_prices(self):
        for rec in self:
            base = PRICE_MAP.get(rec.certificate_type, 0.0)
            shipping = (
                SHIPPING_MAP.get(rec.shipping_type, 0.0)
                if rec.certificate_type in PHYSICAL_TYPES
                else 0.0
            )
            rec.price_base = base
            rec.price_shipping = shipping
            rec.price_total = base + shipping

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains('certificate_type', 'shipping_type')
    def _check_shipping_required(self):
        for rec in self:
            if rec.certificate_type in PHYSICAL_TYPES and not rec.shipping_type:
                raise ValidationError(
                    _('El tipo de envío es obligatorio para certificados físicos.')
                )

    # ------------------------------------------------------------------
    # State transitions (backend buttons)
    # ------------------------------------------------------------------

    def action_cancel(self):
        for rec in self:
            if rec.state in ('done', 'sent'):
                raise UserError(
                    _(
                        'No se puede cancelar el certificado "%s": '
                        'ya está en estado "%s".',
                        rec.name,
                        dict(STATE_SELECTION).get(rec.state),
                    )
                )
            rec.state = 'cancelled'

    def action_mark_in_process(self):
        for rec in self:
            if rec.state != 'paid':
                raise UserError(_('Solo se puede procesar un certificado pagado.'))
            rec.state = 'in_process'

    def action_mark_sent(self):
        """Wizard-less version: opens a simple wizard to enter tracking number."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Marcar como Enviado'),
            'res_model': 'irg.certificate.sent.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_certificate_id': self.id},
        }

    def _do_mark_sent(self, tracking_number=None):
        """Called from irg.certificate.sent.wizard."""
        for rec in self:
            if rec.state != 'in_process':
                raise UserError(
                    _('El certificado debe estar "En Proceso" para marcarse como enviado.')
                )
            rec.write({
                'state': 'sent',
                'delivery_date': fields.Datetime.now(),
                'tracking_number': tracking_number or rec.tracking_number,
            })
            rec._send_sent_notification()

    def action_mark_done(self):
        for rec in self:
            rec.state = 'done'

    # ------------------------------------------------------------------
    # Payment processing
    # ------------------------------------------------------------------

    def _process_payment(self):
        """
        Called by sale.order.action_confirm() hook after payment.
        Digital/custom: generate PDF and mark done.
        Physical: mark paid and queue for admin processing.
        """
        self.ensure_one()
        self.state = 'paid'
        if self.certificate_type in ('digital', 'custom'):
            self._generate_and_attach_pdf()
            self.state = 'done'
            self._send_digital_notification()
        else:
            self._send_paid_notification()

    # ------------------------------------------------------------------
    # PDF generation
    # ------------------------------------------------------------------

    def _generate_and_attach_pdf(self):
        """Render the QWeb PDF and attach it as ir.attachment to this record."""
        self.ensure_one()
        report_ref = 'irg_gradebook_certificates.action_report_certificate'
        try:
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_ref, res_ids=[self.id]
            )
        except Exception as exc:
            _logger.error(
                'Error generando PDF para certificado %s: %s', self.name, exc
            )
            raise UserError(_('No se pudo generar el PDF del certificado. Revisa el log.'))

        filename = 'Certificado_%s_%s.pdf' % (
            (self.partner_id.name or 'Alumno').replace(' ', '_'),
            self.name,
        )
        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
            'public': False,
        })
        self.attachment_id = attachment

    def action_generate_pdf(self):
        """Backend button to (re)generate the PDF."""
        self._generate_and_attach_pdf()

    def action_download_pdf(self):
        """Return file-download action for the attached PDF."""
        self.ensure_one()
        if not self.attachment_id:
            raise UserError(_('No hay PDF generado aún. Genera el certificado primero.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % self.attachment_id.id,
            'target': 'self',
        }

    # ------------------------------------------------------------------
    # Email notifications
    # ------------------------------------------------------------------

    def _send_digital_notification(self):
        template = self.env.ref(
            'irg_gradebook_certificates.mail_template_cert_digital_ready',
            raise_if_not_found=False,
        )
        if template:
            # No force_send to avoid blocking; use queue
            template.send_mail(self.id, force_send=False)

    def _send_paid_notification(self):
        template = self.env.ref(
            'irg_gradebook_certificates.mail_template_cert_paid_physical',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=False)

    def _send_sent_notification(self):
        template = self.env.ref(
            'irg_gradebook_certificates.mail_template_cert_sent',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=False)
