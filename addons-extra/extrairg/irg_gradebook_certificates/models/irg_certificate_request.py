# -*- coding: utf-8 -*-
import base64
import logging
import os
import subprocess
import tempfile

from docx import Document as DocxDocument
from docx.oxml.ns import qn
from copy import deepcopy

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

    # ------------------------------------------------------------------
    # Docx template helpers
    # ------------------------------------------------------------------

    def _get_template_path(self):
        """Return the absolute path to the Word certificate template."""
        module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(
            module_path, 'static', 'src', 'templates',
            'Plantilla-certificado-notas.docx',
        )

    @staticmethod
    def _replace_in_paragraph(paragraph, old, new):
        """Replace *old* with *new* across runs that Word may have split."""
        full = ''.join(r.text for r in paragraph.runs)
        if old not in full:
            return
        full = full.replace(old, new)
        if paragraph.runs:
            paragraph.runs[0].text = full
            for r in paragraph.runs[1:]:
                r.text = ''

    @staticmethod
    def _scale_document_fonts(doc, percent=85):
        """Scale all explicit font sizes in the Word XML by *percent*.

        Word stores font sizes in half-points (e.g. w:val="22" = 11 pt).
        Both w:sz (display) and w:szCs (complex-script) are scaled.
        Minimum enforced: 14 half-points (7 pt) to preserve legibility.
        """
        NS_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        w_val = '{%s}val' % NS_W
        for tag in ('{%s}sz' % NS_W, '{%s}szCs' % NS_W):
            for el in doc.element.iter(tag):
                raw = el.get(w_val)
                if raw and raw.isdigit():
                    new_val = max(14, int(round(int(raw) * percent / 100)))
                    el.set(w_val, str(new_val))

    def _fill_template(self):
        """Open the .docx template, fill placeholders and table, return bytes."""
        self.ensure_one()
        tpl_path = self._get_template_path()
        if not os.path.isfile(tpl_path):
            raise UserError(
                _('No se encuentra la plantilla Word en %s') % tpl_path
            )

        doc = DocxDocument(tpl_path)
        self._scale_document_fonts(doc, percent=85)

        # --- Collect data ---------------------------------------------------
        partner = self.partner_id
        id_label = (
            partner.l10n_latam_identification_type_id.name
            if partner.l10n_latam_identification_type_id
            else 'DNI/Pasaporte'
        )
        documento = '%s %s' % (id_label, partner.vat or '')

        subjects = self.gradebook_student_id.gradebook_subject_ids.filtered(
            lambda s: s.op_subject_id.subject_type == 'compulsory'
        )
        nota_media = '%.2f' % (self.gradebook_student_id.total_final or 0.0)
        fecha = (
            self.request_date.strftime('%d/%m/%Y') if self.request_date else ''
        )

        # --- Replace simple placeholders ------------------------------------
        replacements = {
            '<<nombreAlumno>>': partner.name or '',
            '<<documento>>': documento,
            '<<curso>>': self.course_id.name or '',
            '<<fecha>>': fecha,
        }
        for para in doc.paragraphs:
            for old, new in replacements.items():
                self._replace_in_paragraph(para, old, new)
        # Also check headers
        for section in doc.sections:
            for para in section.header.paragraphs:
                for old, new in replacements.items():
                    self._replace_in_paragraph(para, old, new)

        # --- Fill the grades table (table index 0) --------------------------
        table = doc.tables[0]
        tbl_xml = table._tbl
        all_rows = tbl_xml.findall(qn('w:tr'))
        # Row 0 = header, rows 1‑12 = data slots, row 13 = Nota Media footer
        header_row = all_rows[0]
        data_rows = all_rows[1:-1]   # rows 1..12
        footer_row = all_rows[-1]

        # Fill data rows with subject info
        for idx, row_xml in enumerate(data_rows):
            cells = row_xml.findall(qn('w:tc'))
            if idx < len(subjects):
                subj = subjects[idx]
                cell_values = [
                    subj.op_subject_id.code or '',
                    subj.op_subject_id.name or '',
                    '%.2f' % (subj.final_subject_note or 0.0),
                ]
                for ci, val in enumerate(cell_values):
                    if ci < len(cells):
                        for p in cells[ci].findall(qn('w:p')):
                            for r in p.findall(qn('w:r')):
                                t = r.find(qn('w:t'))
                                if t is not None:
                                    t.text = val
                                    break
                            else:
                                # No run exists — create one
                                r_el = p.makeelement(qn('w:r'), {})
                                rpr_src = data_rows[0].findall(qn('w:tc'))[0] \
                                    .findall(qn('w:p'))[0].findall(qn('w:r'))
                                if rpr_src:
                                    rpr = rpr_src[0].find(qn('w:rPr'))
                                    if rpr is not None:
                                        r_el.append(deepcopy(rpr))
                                t_el = r_el.makeelement(qn('w:t'), {})
                                t_el.text = val
                                r_el.append(t_el)
                                p.append(r_el)
                            break  # only first <w:p>
            else:
                # More rows than subjects → remove the excess row
                tbl_xml.remove(row_xml)

        # If there are more subjects than template rows (>12), clone rows
        if len(subjects) > len(data_rows):
            ref_row = data_rows[0]  # use first data row as formatting reference
            for idx in range(len(data_rows), len(subjects)):
                subj = subjects[idx]
                new_row = deepcopy(ref_row)
                cells = new_row.findall(qn('w:tc'))
                cell_values = [
                    subj.op_subject_id.code or '',
                    subj.op_subject_id.name or '',
                    '%.2f' % (subj.final_subject_note or 0.0),
                ]
                for ci, val in enumerate(cell_values):
                    if ci < len(cells):
                        for p in cells[ci].findall(qn('w:p')):
                            for r in p.findall(qn('w:r')):
                                t = r.find(qn('w:t'))
                                if t is not None:
                                    t.text = val
                                    break
                            break
                footer_row.addprevious(new_row)

        # Fill Nota Media in footer row
        footer_cells = footer_row.findall(qn('w:tc'))
        # Last cell of footer row gets the nota media
        last_cell = footer_cells[-1]
        for p in last_cell.findall(qn('w:p')):
            for r in p.findall(qn('w:r')):
                t = r.find(qn('w:t'))
                if t is not None:
                    t.text = nota_media
                    break
            break

        # Save filled document to a temp file
        tmp_docx = tempfile.NamedTemporaryFile(
            suffix='.docx', delete=False, prefix='cert_'
        )
        doc.save(tmp_docx.name)
        tmp_docx.close()
        return tmp_docx.name

    @staticmethod
    def _convert_to_pdf(docx_path):
        """Convert a .docx file to PDF using LibreOffice and return PDF bytes."""
        out_dir = os.path.dirname(docx_path)
        try:
            subprocess.run(
                [
                    'libreoffice', '--headless', '--norestore',
                    '--convert-to', 'pdf',
                    '--outdir', out_dir,
                    docx_path,
                ],
                check=True,
                timeout=60,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            raise UserError(
                _('LibreOffice no está instalado en el servidor. '
                  'Ejecute: apt-get install -y libreoffice-writer')
            )
        except subprocess.CalledProcessError as exc:
            _logger.error('LibreOffice conversion failed: %s', exc.stderr)
            raise UserError(
                _('Error al convertir el certificado a PDF. Revise el log.')
            )

        pdf_path = docx_path.rsplit('.', 1)[0] + '.pdf'
        if not os.path.isfile(pdf_path):
            raise UserError(_('No se generó el archivo PDF.'))

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        # Cleanup temp files
        for path in (docx_path, pdf_path):
            try:
                os.unlink(path)
            except OSError:
                pass

        return pdf_bytes

    def _generate_and_attach_pdf(self):
        """Fill the Word template with real data and convert to PDF."""
        self.ensure_one()
        try:
            docx_path = self._fill_template()
            pdf_content = self._convert_to_pdf(docx_path)
        except UserError:
            raise
        except Exception as exc:
            _logger.error(
                'Error generando PDF para certificado %s: %s', self.name, exc,
                exc_info=True,
            )
            raise UserError(
                _('No se pudo generar el PDF del certificado. Revise el log.')
            )

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
