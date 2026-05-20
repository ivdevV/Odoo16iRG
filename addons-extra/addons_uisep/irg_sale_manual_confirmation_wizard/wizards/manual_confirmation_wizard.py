# -*- coding: utf-8 -*-
import logging
from datetime import date as date_cls
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


QUARTER_LETTERS = {1: 'A', 2: 'A', 3: 'A',
                   4: 'B', 5: 'B', 6: 'B',
                   7: 'C', 8: 'C', 9: 'C',
                   10: 'D', 11: 'D', 12: 'D'}


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
    batch_preview = fields.Char(
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
                lambda l: l.product_template_id.is_academic_program and l.product_template_id.recurring_invoice
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

        if not order.course_id or not order.product_template_id:
            order.get_academic_product_template_id()

        course_id = order.course_id
        if not course_id:
            warnings.append(_("El presupuesto no tiene curso asignado (order.course_id vacio)."))

        modalidad = self._detect_modalidad(order, course_id)
        if not modalidad:
            warnings.append(_("No se ha podido detectar la modalidad (atributo 'Modalidad' del producto)."))
            modalidad = 'GE'

        date = self.admission_date or fields.Date.today()
        today = fields.Date.today()
        if date.month != today.month or date.year != today.year:
            warnings.append(_(
                "La fecha de admision (%s) no esta en el mes actual (%s). "
                "El codigo de lote se calculara con esa fecha."
            ) % (date, today))

        if modalidad in ('HC', 'PRS') and today.day > 7 and date.month == today.month and date.year == today.year:
            warnings.append(_(
                "Modalidad %s y hoy es dia %s (> 7) en el mismo mes que admission_date: "
                "la logica de irg_openeducat_sale_lote_custom desplazara la fecha al mes siguiente."
            ) % (modalidad, today.day))

        # Preview del codigo
        batch_code = self._build_batch_code_preview(order, course_id, modalidad, date)

        warning_html = ''
        if warnings:
            warning_html = '<ul>' + ''.join('<li>%s</li>' % w for w in warnings) + '</ul>'
        return (modalidad, batch_code, warning_html)

    def _detect_modalidad(self, order, course_id):
        if not course_id:
            return ''
        for line in order.order_line:
            if not self._line_matches(line, course_id):
                continue
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

    def _line_matches(self, line, course_id):
        if hasattr(line.product_id, 'course_id') and line.product_id.course_id.id == course_id.id:
            return True
        if course_id.product_template_id and line.product_id.product_tmpl_id.id == course_id.product_template_id.id:
            return True
        if hasattr(course_id, 'product_template_ids') and line.product_id.product_tmpl_id.id in course_id.product_template_ids.ids:
            return True
        return False

    def _build_batch_code_preview(self, order, course_id, modalidad, date):
        if not course_id:
            return ''
        profix_01 = ''
        if course_id.product_template_id:
            profix_01 = course_id.product_template_id.categ_id.code or ''
        elif hasattr(course_id, 'product_template_ids') and course_id.product_template_ids:
            profix_01 = course_id.product_template_ids[0].categ_id.code or ''
        for line in order.order_line:
            if self._line_matches(line, course_id) and line.product_id.categ_id.code:
                profix_01 = line.product_id.categ_id.code
                break

        prefix_011 = course_id.code or ''
        eff_date = date

        # Replicar shift HC/PRS si procede
        today = fields.Date.today()
        if modalidad in ('HC', 'PRS') and today.day > 7 and date.month == today.month and date.year == today.year:
            eff_date = date + relativedelta(months=1)

        # Si el modulo quarterly esta activo y modalidad = ONL, preview trimestral
        ad = self.env['auto.admission.required'].search([], limit=1)
        quarterly_active = bool(ad and 'quarterly_online_enabled' in ad._fields and ad.quarterly_online_enabled)
        if modalidad == 'ONL' and quarterly_active:
            year = eff_date.strftime('%y')
            return f"{profix_01}{prefix_011}ONL{year}{QUARTER_LETTERS[eff_date.month]}"

        year = eff_date.strftime('%y')
        month = eff_date.strftime('%m')
        return f"{profix_01}{prefix_011}{modalidad}{year}{month}"

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
