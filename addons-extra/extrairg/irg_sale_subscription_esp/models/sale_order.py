# -*- coding: utf-8 -*-
import logging
import re
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _auto_scheduled_order(self):
        """
        Sobrescribe la lógica de programación automática para incluir el cálculo
        de gastos de financiación basado en la diferencia con el precio de contado.
        """
        _logger.info("=== IRG _auto_scheduled_order START for order %s (id=%s) ===", self.name, self.id)

        list_product_comb = []
        TermSchedule = self.env['product.term.schedule'].sudo()
        PaymentTerm = self.env['account.payment.term'].sudo()

        # --- Buscar producto de financiación ---
        financing_product = self.env['product.product'].browse(108)
        if not financing_product.exists():
            financing_product = self.env['product.product'].search(
                [('default_code', '=', 'GASTOS_FIN')], limit=1
            )
        if not financing_product:
            financing_product = self.env.ref(
                'irg_sale_subscription_esp.product_financing_fees', raise_if_not_found=False
            )

        _logger.info("IRG Financing product: %s (id=%s)", 
                      financing_product.name if financing_product else 'NOT FOUND',
                      financing_product.id if financing_product else 'N/A')

        # --- Limpieza: Eliminar líneas de financiación antiguas ---
        if financing_product:
            financing_lines = self.order_line.filtered(
                lambda l: l.product_id.id == financing_product.id
            )
            if financing_lines:
                _logger.info("IRG Removing %d old financing lines", len(financing_lines))
                financing_lines.unlink()

        course_duration = 0

        for ol in self.order_line:
            _logger.info("IRG Processing line: product=%s (id=%s), recurring=%s, price=%s",
                         ol.product_id.name, ol.product_id.id,
                         ol.product_id.recurring_invoice, ol.price_unit)

            if ol.display_type:
                _logger.info("IRG  -> Skipping: display_type line")
                continue
            if financing_product and ol.product_id.id == financing_product.id:
                _logger.info("IRG  -> Skipping: is financing product itself")
                continue

            if ol.product_id.recurring_invoice:

                # === FINANCIACIÓN ===
                try:
                    ptavs = ol.product_id.product_template_attribute_value_ids
                    _logger.info("IRG  -> Product PTAVs: %s",
                                 [(p.attribute_id.name, p.name, p.id) for p in ptavs])

                    ptav_plan = ptavs.filtered(
                        lambda x: x.attribute_id.name and 'planes' in x.attribute_id.name.lower()
                    )
                    _logger.info("IRG  -> Plan PTAVs found: %s",
                                 [(p.attribute_id.name, p.name) for p in ptav_plan])

                    if ptav_plan and financing_product:
                        plan_value = ptav_plan[0]
                        _logger.info("IRG  -> Selected plan: '%s'", plan_value.name)

                        if 'contado' not in plan_value.name.lower():
                            _logger.info("IRG  -> NOT contado, searching for sibling...")

                            # Buscar PAV "Contado"
                            all_plan_values = plan_value.attribute_id.value_ids
                            _logger.info("IRG  -> All values for attribute '%s': %s",
                                         plan_value.attribute_id.name,
                                         [(v.name, v.id) for v in all_plan_values])

                            contado_pav = all_plan_values.filtered(
                                lambda x: 'contado' in x.name.lower()
                            )
                            _logger.info("IRG  -> Contado PAV: %s",
                                         [(v.name, v.id) for v in contado_pav])

                            if contado_pav:
                                # Buscar PTAV para este template
                                contado_ptav = self.env['product.template.attribute.value'].search([
                                    ('product_tmpl_id', '=', ol.product_id.product_tmpl_id.id),
                                    ('product_attribute_value_id', 'in', contado_pav.ids),
                                ], limit=1)
                                _logger.info("IRG  -> Contado PTAV: %s (id=%s)",
                                             contado_ptav.name if contado_ptav else 'NOT FOUND',
                                             contado_ptav.id if contado_ptav else 'N/A')

                                if contado_ptav:
                                    other_ptavs = ptavs.filtered(
                                        lambda x: x.attribute_id.name and 'planes' not in x.attribute_id.name.lower()
                                    )
                                    _logger.info("IRG  -> Other PTAVs: %s",
                                                 [(p.attribute_id.name, p.name, p.id) for p in other_ptavs])

                                    domain = [
                                        ('product_tmpl_id', '=', ol.product_id.product_tmpl_id.id),
                                        ('product_template_attribute_value_ids', 'in', [contado_ptav.id]),
                                    ]
                                    for ptav in other_ptavs:
                                        domain.append(
                                            ('product_template_attribute_value_ids', 'in', [ptav.id])
                                        )

                                    _logger.info("IRG  -> Sibling search domain: %s", domain)
                                    sibling = self.env['product.product'].search(domain, limit=1)
                                    _logger.info("IRG  -> Sibling found: %s (id=%s, price=%s)",
                                                 sibling.name if sibling else 'NOT FOUND',
                                                 sibling.id if sibling else 'N/A',
                                                 sibling.lst_price if sibling else 'N/A')

                                    if sibling:
                                        current_price = ol.price_unit
                                        contado_price = sibling.lst_price

                                        # Si hay tarifa, intentar usarla
                                        if self.pricelist_id:
                                            pricelist_price = self.pricelist_id._get_product_price(
                                                sibling, 1.0
                                            )
                                            if pricelist_price > 0:
                                                contado_price = pricelist_price

                                        _logger.info("IRG  -> current_price=%s, contado_price=%s",
                                                     current_price, contado_price)
                                        fee = current_price - contado_price
                                        _logger.info("IRG  -> fee = %s", fee)

                                        if fee > 0:
                                            _logger.info("IRG  -> APPLYING: update line to %s, create fee line %s", contado_price, fee)
                                            ol.write({'price_unit': contado_price})
                                            self.env['sale.order.line'].create({
                                                'order_id': self.id,
                                                'product_id': financing_product.id,
                                                'name': "Gastos de Financiación (%s) - %s" % (plan_value.name, ol.product_id.name),
                                                'product_uom_qty': ol.product_uom_qty,
                                                'price_unit': fee,
                                                'tax_id': [(6, 0, financing_product.taxes_id.ids)],
                                            })
                                            _logger.info("IRG  -> DONE: Financing line created!")
                                        else:
                                            _logger.info("IRG  -> fee <= 0, no financing needed")
                                    else:
                                        _logger.warning("IRG  -> No contado sibling found!")
                                else:
                                    _logger.warning("IRG  -> No contado PTAV found for template!")
                            else:
                                _logger.warning("IRG  -> No 'contado' value found in attribute values!")
                        else:
                            _logger.info("IRG  -> Plan IS contado, no financing needed")
                    else:
                        if not ptav_plan:
                            _logger.info("IRG  -> No 'Planes' attribute found on product")
                        if not financing_product:
                            _logger.info("IRG  -> No financing product available")

                except Exception as e:
                    _logger.error("IRG  -> EXCEPTION in financing calc: %s", str(e), exc_info=True)

                # === RECOLECCIÓN DE PLAZOS ===
                if ol.product_id.product_template_attribute_value_ids:
                    for ptav in ol.product_id.product_template_attribute_value_ids:
                        if ptav.attribute_id.name and 'planes' in ptav.attribute_id.name.lower():
                            list_product_comb.append(ptav.id)
                            break

                elif ol.product_id.combination_indices:
                    combination_str = str(ol.product_id.combination_indices)
                    if ',' in combination_str:
                        first_id = combination_str.split(',')[0].strip()
                        try:
                            list_product_comb.append(int(first_id))
                        except ValueError:
                            pass
                    else:
                        try:
                            list_product_comb.append(int(combination_str))
                        except ValueError:
                            pass

                if not list_product_comb:
                    courses = False
                    if hasattr(ol.product_id.product_tmpl_id, 'product_template_ids'):
                        courses = ol.product_id.product_tmpl_id.product_template_ids
                    if not courses and hasattr(ol.product_id.product_tmpl_id, 'course_id'):
                        courses = ol.product_id.product_tmpl_id.course_id
                    if courses:
                        for course in courses:
                            if course.duration > course_duration:
                                course_duration = course.duration

        # === CÁLCULO DE PLAZOS ===
        _logger.info("IRG Plazo calc: list_product_comb=%s, course_duration=%s", list_product_comb, course_duration)

        max_plazo = 0
        if list_product_comb:
            attribute = self.env['product.template.attribute.value'].sudo().search(
                [('id', 'in', list_product_comb)]
            )
            plazo_values = attribute.mapped('plazo')
            max_plazo = max(plazo_values) if plazo_values else 0

            if max_plazo == 0:
                max_plazo_str = ','.join(attribute.mapped('name'))
                coincidencias = re.findall(r'\d+', max_plazo_str)
                if coincidencias:
                    plazos = [int(num) for num in coincidencias]
                    max_plazo = max(plazos)
                else:
                    max_plazo = 1

        elif course_duration > 0:
            max_plazo = int(course_duration)
        else:
            max_plazo = 1

        _logger.info("IRG max_plazo = %s", max_plazo)

        if max_plazo > 0:
            term_number_record = TermSchedule.search([('term_number', '=', max_plazo)], limit=1)
            if not term_number_record:
                term_number_record = TermSchedule.search([('custom', '=', True)], limit=1)

            term_number_id = term_number_record.id if term_number_record else False

            payment_term_name = '%s Meses' % max_plazo
            payment_term_record = PaymentTerm.search([('name', '=ilike', payment_term_name)], limit=1)
            if not payment_term_record:
                payment_term_name_02 = '%02d Meses' % max_plazo
                payment_term_record = PaymentTerm.search([('name', '=ilike', payment_term_name_02)], limit=1)

            payment_term_id = payment_term_record.id if payment_term_record else False

            vals = {
                'term_number_id': term_number_id,
                'term_number': max_plazo,
            }
            if payment_term_id:
                vals['payment_term_id'] = payment_term_id

            self.write(vals)
            _logger.info("IRG Written vals: %s", vals)

            # Llamar a funciones de suscripción del módulo extension si existen
            try:
                self.onchange_end_date_suscrip()
            except Exception as e:
                _logger.warning("IRG onchange_end_date_suscrip failed: %s", str(e))

            try:
                self.create_subscription_schedule()
            except Exception as e:
                _logger.warning("IRG create_subscription_schedule failed: %s", str(e))

        _logger.info("=== IRG _auto_scheduled_order END for order %s ===", self.name)
