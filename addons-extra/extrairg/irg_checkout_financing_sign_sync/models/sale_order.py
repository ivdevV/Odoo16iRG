# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import time

from odoo import models, fields, api


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    irg_forma_pago = fields.Char(string='Forma de pago (web)', copy=False)
    irg_primer_vencimiento = fields.Date(string='Primer vencimiento (web)', copy=False)
    irg_matricula_pago_inicial = fields.Float(string='Matrícula/Pago inicial (web)', copy=False)

    def _create_payment_transaction(self, vals):
        self.ensure_one()

        provider_code = False
        provider_id = vals.get('provider_id')
        if provider_id:
            provider = self.env['payment.provider'].sudo().browse(provider_id)
            provider_code = provider.code if provider.exists() else False

        is_stripe_checkout = provider_code in (False, 'stripe')
        if is_stripe_checkout and (self.term_number or 0) > 1 and (self.amount_total or 0.0) > 0:
            installment_amount = self.currency_id.round(self.amount_total / self.term_number)
            if installment_amount > 0:
                vals['amount'] = installment_amount

        return super(SaleOrder, self)._create_payment_transaction(vals)

    def _auto_scheduled_order(self):
        start_all = time.perf_counter()
        super_start = time.perf_counter()
        res = super(SaleOrder, self)._auto_scheduled_order()
        _logger.info("IRG _auto_scheduled_order: super() in %.3fs", time.perf_counter() - super_start)

        for order in self:
            per_start = time.perf_counter()
            try:
                had_financing = bool(order.order_line.filtered(lambda l: l.irg_line_type == 'financing'))

                ensure_start = time.perf_counter()
                order._irg_ensure_financing_lines_consistent()
                _logger.info(
                    "IRG _auto_scheduled_order: ensure consistent in %.3fs (order=%s)",
                    time.perf_counter() - ensure_start,
                    order.name,
                )
                has_financing_now = bool(order.order_line.filtered(lambda l: l.irg_line_type == 'financing'))

                if (
                    not had_financing
                    and has_financing_now
                    and (order.term_number or 0) > 1
                    and order.recurrence_id
                    and order.start_date
                    and order.end_date
                ):
                    schedule_start = time.perf_counter()
                    order.create_subscription_schedule()
                    _logger.info(
                        "IRG _auto_scheduled_order: create_subscription_schedule in %.3fs (order=%s)",
                        time.perf_counter() - schedule_start,
                        order.name,
                    )
            except Exception as exc:
                _logger.exception(
                    "IRG post _auto_scheduled_order consistency failed for order %s: %s",
                    order.name,
                    exc,
                )
            finally:
                per_elapsed = time.perf_counter() - per_start
                _logger.info("IRG _auto_scheduled_order: order %s processed in %.3fs", order.name, per_elapsed)

        total_elapsed = time.perf_counter() - start_all
        _logger.info("IRG _auto_scheduled_order: processed %s orders in %.3fs", len(self), total_elapsed)
        return res

    academic_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Documentación académica',
        compute='_compute_academic_attachment_ids',
        readonly=True,
    )
    academic_attachment_count = fields.Integer(
        string='Nº documentos académicos',
        compute='_compute_academic_attachment_ids',
        readonly=True,
    )

    @api.depends('message_attachment_count')
    def _compute_academic_attachment_ids(self):
        attachment_model = self.env['ir.attachment'].sudo()
        for order in self:
            attachments = attachment_model.search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id),
                ('description', 'ilike', 'Documentación académica subida desde ecommerce'),
            ], order='create_date desc')
            order.academic_attachment_ids = attachments
            order.academic_attachment_count = len(attachments)

    def _irg_ensure_financing_lines_consistent(self):
        """
        Safety fallback for checkout pages:
        if a financed product has no financing line, recreate it from the
        difference between the financed variant and its contado sibling.
        Uses the same product lookup chain as _auto_scheduled_order.
        """
        lookup_start = time.perf_counter()
        financing_product = self.env.ref(
            'irg_sale_subscription_esp.product_financing_fees',
            raise_if_not_found=False,
        )
        if not financing_product:
            financing_product = self.env['product.product'].search(
                [('default_code', '=', 'GASTOS_FIN')], limit=1,
            )
        if not financing_product:
            candidate = self.env['product.product'].browse(108)
            financing_product = candidate if candidate.exists() else False
        if not financing_product:
            return
        _logger.info(
            "IRG _irg_ensure_financing_lines_consistent: financing product lookup %.3fs (product_id=%s)",
            time.perf_counter() - lookup_start,
            financing_product.id,
        )

        overall_start = time.perf_counter()
        for order in self:
            start = time.perf_counter()
            try:
                for line in order.order_line.filtered(
                    lambda l: not l.display_type
                    and l.irg_line_type not in ('financing', 'matricula', 'matricula_discount')
                ):
                    line_start = time.perf_counter()
                    plan_ptav = line.product_id.product_template_attribute_value_ids.filtered(
                        lambda x: x.attribute_id.name == 'Planes'
                    )
                    plan_ptav = plan_ptav[0] if plan_ptav else False

                    is_financed_plan = bool(plan_ptav and 'contado' not in (plan_ptav.name or '').lower())
                    is_multiterm_master = bool((order.term_number or 0) > 1 and line.irg_line_type == 'master')
                    if not (is_financed_plan or is_multiterm_master):
                        continue

                    sibling_contado = order._irg_get_sibling_contado(line.product_id)
                    if not sibling_contado:
                        continue

                    # Usar recurrence=None para evitar inconsistencias entre re-ejecuciones
                    price_start = time.perf_counter()
                    financed_price = order._irg_get_variant_order_price(
                        line.product_id,
                        recurrence=None,
                        pricelist=order.pricelist_id,
                    )
                    contado_price = order._irg_get_variant_order_price(
                        sibling_contado,
                        recurrence=None,
                        pricelist=order.pricelist_id,
                    )
                    _logger.info(
                        "IRG ensure_consistent: price lookup %.3fs (order=%s line=%s)",
                        time.perf_counter() - price_start,
                        order.name,
                        line.id,
                    )

                    plan_extra = (plan_ptav.price_extra or 0.0) if plan_ptav else 0.0
                    contado_ptav = line.product_id.product_tmpl_id.attribute_line_ids.filtered(
                        lambda attr_line: plan_ptav and attr_line.attribute_id.id == plan_ptav.attribute_id.id
                    ).product_template_value_ids.filtered(
                        lambda value: 'contado' in (value.name or '').lower()
                    )
                    contado_extra = contado_ptav[0].price_extra if contado_ptav else 0.0

                    # Nivel 3: lst_price de las variantes
                    lst_financed = line.product_id.lst_price
                    lst_contado = sibling_contado.lst_price

                    financing_fee_unit = financed_price - contado_price
                    if financing_fee_unit <= 0:
                        financing_fee_unit = plan_extra - contado_extra
                    if financing_fee_unit <= 0:
                        financing_fee_unit = lst_financed - lst_contado
                    if financing_fee_unit <= 0:
                        # Preservar línea existente si ya existe con fee > 0
                        existing = order.order_line.filtered(
                            lambda ln: ln.irg_line_type == 'financing' and ln.irg_parent_line_id == line
                        )
                        if existing and existing[0].price_unit > 0:
                            _logger.info("IRG ensure_consistent: fee=0 but preserving existing financing line %s (price_unit=%s)", existing[0].id, existing[0].price_unit)
                        continue

                    write_start = time.perf_counter()
                    line.write({
                        'price_unit': contado_price,
                        'irg_force_price_unit': contado_price,
                        'irg_force_price_unit_set': True,
                        'irg_line_type': 'master',
                    })
                    _logger.info(
                        "IRG ensure_consistent: master line.write %.3fs (order=%s line=%s)",
                        time.perf_counter() - write_start,
                        order.name,
                        line.id,
                    )

                    existing_fin_lines = order.order_line.filtered(
                        lambda ln: ln.irg_line_type == 'financing' and ln.irg_parent_line_id == line
                    )
                    fin_name = "Gastos de Financiación (%s) - %s" % (
                        (plan_ptav and plan_ptav.name) or ('%s meses' % (order.term_number or 1)),
                        line.product_id.name,
                    )
                    fin_write_start = time.perf_counter()
                    if existing_fin_lines:
                        fin_line = existing_fin_lines[0]
                        (existing_fin_lines - fin_line).unlink()
                        fin_line.write({
                            'name': fin_name,
                            'product_uom_qty': line.product_uom_qty,
                            'price_unit': financing_fee_unit,
                            'irg_force_price_unit': financing_fee_unit,
                            'irg_force_price_unit_set': True,
                            'tax_id': [(6, 0, financing_product.taxes_id.ids)],
                        })
                    else:
                        self.env['sale.order.line'].sudo().create({
                            'order_id': order.id,
                            'product_id': financing_product.id,
                            'name': fin_name,
                            'product_uom_qty': line.product_uom_qty,
                            'price_unit': financing_fee_unit,
                            'irg_force_price_unit': financing_fee_unit,
                            'irg_force_price_unit_set': True,
                            'tax_id': [(6, 0, financing_product.taxes_id.ids)],
                            'irg_line_type': 'financing',
                            'irg_parent_line_id': line.id,
                        })
                    _logger.info(
                        "IRG ensure_consistent: financing line write/create %.3fs (order=%s line=%s)",
                        time.perf_counter() - fin_write_start,
                        order.name,
                        line.id,
                    )
                    _logger.info(
                        "IRG ensure_consistent: full line processing %.3fs (order=%s line=%s)",
                        time.perf_counter() - line_start,
                        order.name,
                        line.id,
                    )
            finally:
                elapsed = time.perf_counter() - start
                _logger.info("IRG _irg_ensure_financing_lines_consistent: order %s processed in %.3fs", order.name, elapsed)
        total = time.perf_counter() - overall_start
        _logger.info("IRG _irg_ensure_financing_lines_consistent: processed %s orders in %.3fs", len(self), total)

    def _process_custom_form(self, partner_id, form_data):
        """
        Completa la sincronización de campos web -> partner/sale.order
        para que el reporte de matrícula no quede con huecos.
        """
        res = super(SaleOrder, self)._process_custom_form(partner_id, form_data)
        if not form_data:
            return res

        data_dict = {}
        for row in form_data.split('\n'):
            if ' : ' in row:
                key, value = row.split(' : ', 1)
                data_dict[key.strip()] = value.strip()

        partner = partner_id if hasattr(partner_id, '_name') else self.env['res.partner'].browse(partner_id or self.partner_id.id)
        partner = partner.sudo()

        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, '%d/%m/%Y').date()
            except Exception:
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except Exception:
                    return False

        def parse_float(value):
            if not value:
                return 0.0
            normalized = str(value).replace('€', '').replace(' ', '').replace('.', '').replace(',', '.')
            try:
                return float(normalized)
            except Exception:
                return 0.0

        finalizacion = parse_date(data_dict.get('finalizacionestudios', ''))
        graduation_year_input = data_dict.get('graduation_year')
        graduation_year = str(finalizacion.year) if finalizacion else False
        if graduation_year_input:
            graduation_year = str(graduation_year_input).strip()
        phone = data_dict.get('phone')
        profession = data_dict.get('profession')
        university = data_dict.get('university')
        titulacion = data_dict.get('titulacion')
        vat = data_dict.get('vat')
        forma_pago = data_dict.get('forma_pago')
        primer_vencimiento = parse_date(data_dict.get('primer_vencimiento', ''))
        matricula_pago_inicial = parse_float(data_dict.get('matricula_pago_inicial'))

        partner_vals = {}
        if vat and 'vat' in partner._fields:
            partner_vals['vat'] = vat
        if phone:
            if 'phone' in partner._fields:
                partner_vals['phone'] = phone
            if 'mobile' in partner._fields:
                partner_vals['mobile'] = phone
        if profession:
            if 'profession' in partner._fields:
                partner_vals['profession'] = profession
            if 'function' in partner._fields:
                partner_vals['function'] = profession
        if university:
            if 'university' in partner._fields:
                partner_vals['university'] = university
            if 'x_studio_universidad' in partner._fields:
                partner_vals['x_studio_universidad'] = university
        if titulacion:
            if 'titulacion' in partner._fields:
                partner_vals['titulacion'] = titulacion
            if 'x_studio_titulacion' in partner._fields:
                partner_vals['x_studio_titulacion'] = titulacion
        if graduation_year and 'x_studio_ano_de_graduacion' in partner._fields:
            partner_vals['x_studio_ano_de_graduacion'] = graduation_year

        if partner_vals:
            partner.write(partner_vals)

        student = self.student_id.sudo() if self.student_id else False
        if student and student.id != partner.id:
            student_vals = {key: value for key, value in partner_vals.items() if key in student._fields}
            if student_vals:
                student.write(student_vals)

        order_vals = {}
        if forma_pago and 'irg_forma_pago' in self._fields:
            order_vals['irg_forma_pago'] = forma_pago
        if primer_vencimiento and 'irg_primer_vencimiento' in self._fields:
            order_vals['irg_primer_vencimiento'] = primer_vencimiento
        if 'irg_matricula_pago_inicial' in self._fields:
            order_vals['irg_matricula_pago_inicial'] = matricula_pago_inicial
        if order_vals:
            self.sudo().write(order_vals)

        return res
