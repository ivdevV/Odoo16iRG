# -*- coding: utf-8 -*-
import logging
from datetime import date as date_cls
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


QUARTER_LETTERS = {1: '1', 2: '1', 3: '1',
                   4: '2', 5: '2', 6: '2',
                   7: '3', 8: '3', 9: '3',
                   10: '4', 11: '4', 12: '4'}


class ManualConfirmationWizard(models.TransientModel):
    _name = 'irg.manual.confirmation.wizard'
    _description = 'Wizard de confirmacion manual de presupuestos'

    order_id = fields.Many2one('sale.order', string='Presupuesto', required=True, ondelete='cascade')
    admission_date = fields.Date(
        string='Fecha de Admision',
        required=True,
        help='Fecha que se usara para generar el codigo del lote y los calculos de periodo.',
    )
    modalidad_detected = fields.Char(
        string='Modalidad detectada',
        compute='_compute_preview',
        store=False,
    )
    batch_preview = fields.Text(
        string='Lote previsto',
        compute='_compute_preview',
        store=False,
    )
    warning_message = fields.Html(
        string='Avisos',
        compute='_compute_preview',
        store=False,
    )

    # ----------------------------------------------------------------
    # Defaults
    # ----------------------------------------------------------------

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order_id = res.get('order_id') or self.env.context.get('default_order_id')
        if order_id:
            order = self.env['sale.order'].browse(order_id)
            academic_lines = order.order_line.filtered(
                lambda l: (l.product_template_id.is_academic_program and l.product_template_id.recurring_invoice) or
                          self.env['op.course'].search_count([
                              '|',
                              ('product_template_id', '=', l.product_template_id.id),
                              ('product_template_ids', 'in', l.product_template_id.id)
                          ]) > 0
            )
            line_start_date = False
            if academic_lines:
                line_start_date = academic_lines[0].start_date_enroller
            
            if line_start_date:
                res['admission_date'] = line_start_date
            else:
                today = fields.Date.today()
                current_admission = order.admission_date
                if not current_admission or current_admission.month != today.month or current_admission.year != today.year:
                    res['admission_date'] = today.replace(day=1)
                else:
                    res['admission_date'] = current_admission
        return res

    # ----------------------------------------------------------------
    # Compute
    # ----------------------------------------------------------------

    @api.depends('admission_date', 'order_id')
    def _compute_preview(self):
        for wiz in self:
            modalidad, batch_code, warnings = wiz._build_preview()
            wiz.modalidad_detected = modalidad
            wiz.batch_preview = batch_code
            wiz.warning_message = warnings

    def _build_preview(self):
        self.ensure_one()
        order = self.order_id
        warnings = []
        if not order:
            return ('', '', '')

        academic_lines = order.order_line.filtered(
            lambda l: (l.product_template_id.is_academic_program and l.product_template_id.recurring_invoice) or
                      self.env['op.course'].search_count([
                          '|',
                          ('product_template_id', '=', l.product_template_id.id),
                          ('product_template_ids', 'in', l.product_template_id.id)
                      ]) > 0
        )
        if not academic_lines:
            return ('', '', '')

        modalities = []
        batch_previews = []
        today = fields.Date.today()
        date = self.admission_date or today

        if date.month != today.month or date.year != today.year:
            warnings.append(_(
                "La fecha de admision general (%s) no esta en el mes actual (%s). "
                "El codigo de lote se calculara con esa fecha si no hay fecha especifica en la linea."
            ) % (date, today))

        for line in academic_lines:
            course_id = self._find_course_for_line(line)
            if not course_id:
                warnings.append(_("El producto %s no tiene curso asignado.") % line.product_template_id.name)
                continue

            modality = self._detect_line_modalidad(line, course_id)
            if not modality:
                warnings.append(_("No se ha podido detectar la modalidad para el producto %s.") % line.product_template_id.name)
                modality = 'GE'

            line_date = line.start_date_enroller or date

            if modality in ('HC', 'PRS') and today.day > 7 and line_date.month == today.month and line_date.year == today.year:
                warnings.append(_(
                    "Modalidad %s para %s y hoy es dia %s (> 7) en el mismo mes que la fecha del lote (%s): "
                    "la logica de irg_openeducat_sale_lote_custom desplazara la fecha al mes siguiente."
                ) % (modality, line.product_template_id.name, today.day, line_date))

            batch_code = self._build_line_batch_code_preview(line, course_id, modality, line_date)

            if modality not in modalities:
                modalities.append(modality)
            batch_previews.append(f"{line.product_template_id.name}: {batch_code}")

        warning_html = ''
        if warnings:
            warning_html = '<ul>' + ''.join('<li>%s</li>' % w for w in warnings) + '</ul>'

        return (', '.join(modalities), '\n'.join(batch_previews), warning_html)

    def _find_course_for_line(self, line):
        domain = ['|', 
                 ('product_template_id', '=', line.product_template_id.id),
                 ('product_template_ids', 'in', line.product_template_id.id)]
        return self.env['op.course'].search(domain, limit=1)

    def _detect_line_modalidad(self, line, course_id):
        if not course_id:
            return ''
        for ptav in line.product_id.product_template_attribute_value_ids:
            if ptav.attribute_id.name == 'Modalidad':
                name = (ptav.product_attribute_value_id.name or '').strip()
                if name == 'Online':
                    return 'ONL'
                if name == 'HomeClass':
                    return 'HC'
                if name == 'Presencial':
                    return 'PRS'
                return name[:3].upper() if name else 'GE'
        return 'GE'

    def _build_line_batch_code_preview(self, line, course_id, modality, date):
        if not course_id:
            return ''
        
        # Category code (profix_01)
        profix_01 = line.product_id.categ_id.code or ''
        if not profix_01:
            if course_id.product_template_id:
                profix_01 = course_id.product_template_id.categ_id.code or ''
            elif hasattr(course_id, 'product_template_ids') and course_id.product_template_ids:
                profix_01 = course_id.product_template_ids[0].categ_id.code or ''

        # Detect if bonificado (price <= 0) - ONLY FOR ONL modality
        is_bonificado = line.price_unit <= 0 or line.price_subtotal <= 0
        if is_bonificado and modality == 'ONL' and profix_01.startswith('M'):
            profix_01 = 'M' + 'B' + profix_01[1:]

        course_code = course_id.code or ''
        eff_date = date

        # Replicar shift HC/PRS si procede
        today = fields.Date.today()
        if modality in ('HC', 'PRS') and today.day > 7 and date.month == today.month and date.year == today.year:
            eff_date = date + relativedelta(months=1)

        # Si el modulo quarterly esta activo y modalidad = ONL, preview trimestral
        ad = self.env['auto.admission.required'].search([], limit=1)
        quarterly_active = bool(ad and 'quarterly_online_enabled' in ad._fields and ad.quarterly_online_enabled)
        
        if modality == 'ONL' and quarterly_active:
            quarter = str((eff_date.month - 1) // 3 + 1)
            year = eff_date.strftime('%y')
            return f"{profix_01}{course_code}ONL{year}{quarter}"

        year = eff_date.strftime('%y')
        month = eff_date.strftime('%m')
        return f"{profix_01}{course_code}{modality}{year}{month}"

    # ----------------------------------------------------------------
    # Actions
    # ----------------------------------------------------------------

    def action_confirm(self):
        self.ensure_one()
        order = self.order_id
        if not order:
            raise UserError(_("No hay presupuesto asociado al wizard."))

        # Aplicar admission_date elegida
        if order.admission_date != self.admission_date:
            _logger.info(
                "IRG Manual Wizard: ajustando admission_date de %s a %s en SO %s",
                order.admission_date, self.admission_date, order.name,
            )
            order.admission_date = self.admission_date

        return order.with_context(irg_manual_wizard_passed=True).action_confirm()
