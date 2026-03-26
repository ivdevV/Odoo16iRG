# -*- coding: utf-8 -*-
import logging
import re
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

_UNSET = object()  # sentinel to distinguish "not passed" from explicit None


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _irg_get_variant_order_price(self, product, recurrence=_UNSET, pricelist=None):
        """Return unit price for a product variant in current order context.

        Priority:
        1) product.pricing with same variant + pricelist + recurrence
        2) product.pricing variant + no pricelist + recurrence
        3) product.pricing template-level + variant price_extra
        4) pricelist._get_product_price (includes price_extra from attributes)
        5) fallback product.lst_price of that exact variant

        Pass recurrence=None to explicitly skip recurrence filtering.
        """
        self.ensure_one()
        if not product:
            return 0.0

        # recurrence=_UNSET → use order's recurrence; recurrence=None → no filter
        if recurrence is _UNSET:
            recurrence = self.recurrence_id
        pricelist = pricelist or self.pricelist_id

        pricing_domain = [
            ('product_template_id', '=', product.product_tmpl_id.id),
        ]
        if recurrence:
            pricing_domain.append(('recurrence_id', '=', recurrence.id))

        pricing_rules = self.env['product.pricing'].search(pricing_domain)
        if pricing_rules:
            # 1) Rules specific to this variant
            variant_rules = pricing_rules.filtered(lambda rule: product in rule.product_variant_ids)

            def _pick(rules):
                if not rules:
                    return False
                if pricelist:
                    with_pricelist = rules.filtered(lambda r: r.pricelist_id == pricelist)
                    if with_pricelist:
                        return with_pricelist[0]
                no_pricelist = rules.filtered(lambda r: not r.pricelist_id)
                if no_pricelist:
                    return no_pricelist[0]
                return rules[0]

            selected_rule = _pick(variant_rules)
            if selected_rule:
                return selected_rule.price

            # 2) Template-level rules (no variant restriction): add variant
            # price_extra so each variant gets a distinct price.
            template_rules = pricing_rules.filtered(lambda rule: not rule.product_variant_ids)
            selected_template_rule = _pick(template_rules)
            if selected_template_rule:
                variant_extra = sum(
                    product.product_template_attribute_value_ids.mapped('price_extra')
                )
                return selected_template_rule.price + variant_extra

        # Fallback: pricelist computation (respects price_extra from attributes)
        if pricelist:
            try:
                price = pricelist._get_product_price(product, 1.0)
                if price and price > 0:
                    return price
            except Exception:
                pass

        return product.lst_price

    def _irg_get_sibling_contado(self, product):
        """Find the exact contado sibling variant for a financed variant."""
        self.ensure_one()
        if not product:
            return self.env['product.product']

        plan_ptav = product.product_template_attribute_value_ids.filtered(
            lambda x: x.attribute_id.name == 'Planes'
        )
        if not plan_ptav:
            return self.env['product.product']

        plan_ptav = plan_ptav[0]
        contado_values = plan_ptav.attribute_id.value_ids.filtered(
            lambda x: 'contado' in (x.name or '').lower()
        )
        if not contado_values:
            return self.env['product.product']

        other_ptav_ids = set(
            product.product_template_attribute_value_ids.filtered(
                lambda x: x.attribute_id.name != 'Planes'
            ).ids
        )

        candidates = self.env['product.product'].search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('product_template_attribute_value_ids.product_attribute_value_id', 'in', contado_values.ids),
        ])
        for candidate in candidates:
            candidate_other_ids = set(
                candidate.product_template_attribute_value_ids.filtered(
                    lambda x: x.attribute_id.name != 'Planes'
                ).ids
            )
            if candidate_other_ids == other_ptav_ids:
                return candidate

        return self.env['product.product']

    def _auto_scheduled_order(self):
        """
        Sobrescribe la lógica de programación automática para incluir el cálculo
        de gastos de financiación basado en la diferencia con el precio de contado.
        """
        _logger.info("--- START IRG ESP _auto_scheduled_order for order %s ---", self.name)
        
        list_product_comb = []
        TermSchedule = self.env['product.term.schedule'].sudo()
        PaymentTerm = self.env['account.payment.term'].sudo()
        financing_product = self.env.ref('irg_sale_subscription_esp.product_financing_fees', raise_if_not_found=False)
        matricula_product = self.env['product.product'].search(
            [('default_code', '=', 'MATRICULA')], limit=1
        )
        if not matricula_product:
            matricula_product = self.env['product.product'].search(
                [('name', 'ilike', 'Matricula')], limit=1
            )
        
        if not financing_product:
            financing_product = self.env['product.product'].search([('default_code', '=', 'GASTOS_FIN')], limit=1)
            
        if not financing_product:
             # Fallback: ID proporcionado explícitamente
             financing_product = self.env['product.product'].browse(108)
             if not financing_product.exists():
                 financing_product = False

        # 1. NO borrar líneas de financiación aquí. Se actualizan/crean abajo de forma idempotente.

        # Variable para almacenar la duración del curso si no hay atributos
        course_duration = 0

        for ol in self.order_line:
            # Ignoramos líneas de nota/sección o el propio producto de financiación
            if ol.display_type or (financing_product and ol.product_id == financing_product):
                continue
            # Ignorar líneas de matrícula
            if ol.irg_line_type in ('matricula', 'matricula_discount'):
                continue
                
            if ol.product_id.recurring_invoice:
                
                # --- LÓGICA DE FINANCIACIÓN ---
                # Buscamos si tiene atributo "Planes"
                ptav_plan = ol.product_id.product_template_attribute_value_ids.filtered(lambda x: x.attribute_id.name == 'Planes')
                
                if ptav_plan and financing_product:
                    # Asumimos un solo valor para planes
                    plan_value = ptav_plan[0]
                    
                    # Si NO es Contado, calculamos la diferencia
                    if 'contado' not in plan_value.name.lower():
                        _logger.info("Producto financiado detectado: %s - Plan: %s", ol.product_id.name, plan_value.name)
                        
                        # 1. Buscar la variante "Contado" hermana exacta
                        sibling_contado = self._irg_get_sibling_contado(ol.product_id)

                        if sibling_contado:
                                # Mark the main line so we can order the summary consistently
                                if ol.irg_line_type != 'master':
                                    ol.write({'irg_line_type': 'master'})

                                # === CÁLCULO DE FEE ===
                                # Usar SIEMPRE sin recurrence para evitar inconsistencia entre ejecuciones
                                financed_price = self._irg_get_variant_order_price(
                                    ol.product_id,
                                    recurrence=None,
                                    pricelist=self.pricelist_id,
                                )
                                contado_price = self._irg_get_variant_order_price(
                                    sibling_contado,
                                    recurrence=None,
                                    pricelist=self.pricelist_id,
                                )
                                _logger.info("IRG Financiación [PRICING RULES sin recurrence]: financed=%s, contado=%s, diff=%s",
                                             financed_price, contado_price, financed_price - contado_price)

                                # Nivel 2: price_extra directos del atributo Planes
                                plan_extra = ptav_plan[0].price_extra or 0.0
                                contado_ptav = ol.product_id.product_tmpl_id.attribute_line_ids.filtered(
                                    lambda l: l.attribute_id.id == ptav_plan[0].attribute_id.id
                                ).product_template_value_ids.filtered(
                                    lambda v: 'contado' in (v.name or '').lower()
                                )
                                contado_extra = contado_ptav[0].price_extra if contado_ptav else 0.0
                                _logger.info("IRG Financiación [PRICE_EXTRA]: plan_extra=%s, contado_extra=%s, diff=%s",
                                             plan_extra, contado_extra, plan_extra - contado_extra)

                                # Nivel 3: lst_price de las variantes (incluye price_extra del ORM)
                                lst_financed = ol.product_id.lst_price
                                lst_contado = sibling_contado.lst_price
                                _logger.info("IRG Financiación [LST_PRICE]: financed=%s, contado=%s, diff=%s",
                                             lst_financed, lst_contado, lst_financed - lst_contado)

                                # === DECIDIR FEE: usar la primera fuente que dé un resultado positivo ===
                                financing_fee_unit = financed_price - contado_price
                                fee_source = "PRICING_RULES"
                                if financing_fee_unit <= 0:
                                    financing_fee_unit = plan_extra - contado_extra
                                    fee_source = "PRICE_EXTRA"
                                if financing_fee_unit <= 0:
                                    financing_fee_unit = lst_financed - lst_contado
                                    fee_source = "LST_PRICE"

                                _logger.info("IRG Financiación FINAL: fee=%s (fuente: %s)",
                                             financing_fee_unit, fee_source)

                                # Buscar líneas existentes para esta línea master
                                existing_fin_lines = self.order_line.filtered(
                                    lambda l: l.irg_line_type == 'financing' and l.irg_parent_line_id == ol
                                )
                                # También buscar por producto de financiación sin parent (legacy)
                                if not existing_fin_lines and financing_product:
                                    existing_fin_lines = self.order_line.filtered(
                                        lambda l: l.product_id == financing_product and l.irg_line_type != 'master'
                                    )

                                if financing_fee_unit > 0:
                                    _logger.info("IRG Aplicando financiación. Diferencia unitaria: %s", financing_fee_unit)

                                    # Precio contado fijo
                                    line_contado_price = contado_price if contado_price > 0 else lst_contado

                                    # 2. Actualizar línea actual al precio de contado
                                    ol.write({
                                        'price_unit': line_contado_price,
                                        'irg_force_price_unit': line_contado_price,
                                        'irg_force_price_unit_set': True,
                                    })

                                    # 3. Crear o actualizar línea de gastos de financiación
                                    fin_name = f"Gastos de Financiación ({plan_value.name}) - {ol.product_id.name}"
                                    if existing_fin_lines:
                                        fin_line = existing_fin_lines[0]
                                        (existing_fin_lines - fin_line).unlink()
                                        fin_line.write({
                                            'name': fin_name,
                                            'product_uom_qty': ol.product_uom_qty,
                                            'price_unit': financing_fee_unit,
                                            'irg_force_price_unit': financing_fee_unit,
                                            'irg_force_price_unit_set': True,
                                            'tax_id': [(6, 0, financing_product.taxes_id.ids)],
                                            'irg_line_type': 'financing',
                                            'irg_parent_line_id': ol.id,
                                        })
                                        _logger.info("IRG: updated existing financing line %s (price_unit=%s) on order %s", fin_line.id, financing_fee_unit, self.name)
                                    else:
                                        _logger.info("IRG: about to create financing line for order %s (product %s), fee_unit=%s", self.name, financing_product.default_code or financing_product.id, financing_fee_unit)
                                        fin_line = self.env['sale.order.line'].sudo().create({
                                            'order_id': self.id,
                                            'product_id': financing_product.id,
                                            'name': fin_name,
                                            'product_uom_qty': ol.product_uom_qty,
                                            'price_unit': financing_fee_unit,
                                            'irg_force_price_unit': financing_fee_unit,
                                            'irg_force_price_unit_set': True,
                                            'tax_id': [(6, 0, financing_product.taxes_id.ids)],
                                            'irg_line_type': 'financing',
                                            'irg_parent_line_id': ol.id,
                                        })
                                        if fin_line:
                                            _logger.info("IRG: created financing line %s (qty=%s, price_unit=%s) on order %s", fin_line.id, fin_line.product_uom_qty, fin_line.price_unit, self.name)
                                            try:
                                                self.message_post(body=(f"IRG: Financing line created (id={fin_line.id}) - qty={fin_line.product_uom_qty}, unit_price={fin_line.price_unit} for order {self.name}"))
                                            except Exception as e:
                                                _logger.exception("IRG: failed to post message on order %s: %s", self.name, e)

                                    # Add Matricula line per master line (idempotente)
                                    existing_matricula_lines = self.order_line.filtered(
                                        lambda l: l.irg_parent_line_id == ol and l.irg_line_type == 'matricula'
                                    )
                                    if not existing_matricula_lines:
                                        matricula_vals = {
                                            'order_id': self.id,
                                            'name': "Matricula (BONIFICADA 100%)",
                                            'product_uom_qty': 1.0,
                                            'price_unit': 0.0,
                                            'irg_line_type': 'matricula',
                                            'irg_parent_line_id': ol.id,
                                        }
                                        if matricula_product:
                                            matricula_vals.update({
                                                'product_id': matricula_product.id,
                                                'tax_id': [(6, 0, matricula_product.taxes_id.ids)],
                                                'irg_force_price_unit': 0.0,
                                                'irg_force_price_unit_set': True,
                                            })
                                        else:
                                            matricula_vals.update({
                                                'display_type': 'line_note',
                                            })
                                        self.env['sale.order.line'].sudo().create(matricula_vals)

                                else:
                                    # Fee <= 0: preservar línea existente si la hay (evitar perder datos entre re-ejecuciones)
                                    if existing_fin_lines:
                                        _logger.info("IRG: fee calculado <= 0 pero línea de financiación existente preservada (price_unit=%s) en order %s",
                                                     existing_fin_lines[0].price_unit, self.name)
                                    else:
                                        _logger.info("IRG: fee calculado <= 0, sin línea de financiación existente para order %s", self.name)
                        else:
                            _logger.warning("No se encontró variante Contado para %s", ol.product_id.name)

                # --- FIN LÓGICA FINANCIACIÓN ---

                # Recolección de datos para plazos (Lógica original preservada/mejorada)
                if ol.product_id.product_template_attribute_value_ids:
                    for ptav in ol.product_id.product_template_attribute_value_ids:
                        if ptav.attribute_id.name == 'Planes':
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

                # Fallback duration
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

        # --- CÁLCULO DE PLAZOS ---
        max_plazo = 0
        if list_product_comb:
            attribute = self.env['product.template.attribute.value'].sudo().search([('id', 'in', list_product_comb)])
            max_plazo = max(attribute.mapped('plazo')) if attribute.mapped('plazo') else 0
            
            if max_plazo == 0:
                max_plazo_str = attribute.mapped('name')
                max_plazo_str = ','.join(max_plazo_str)                    
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

        term_number_record = TermSchedule.search([('term_number', '=', max_plazo)], limit=1)
        if not term_number_record:
             term_number_record = TermSchedule.search([('custom','=',True)], limit=1)
        
        term_number_id = term_number_record.id if term_number_record else False

        payment_term_name = f'{max_plazo} Meses'
        payment_term_record = PaymentTerm.search([('name', '=', payment_term_name)], limit=1)
        
        if not payment_term_record:
             payment_term_record = PaymentTerm.search([('name', 'ilike', payment_term_name)], limit=1)

        payment_term_id = payment_term_record.id if payment_term_record else False
        
        # Recurrence setup
        recurrence_record = False
        Recurrence = self.env['sale.temporal.recurrence']
        if max_plazo > 1:
            recurrence_record = Recurrence.search([('duration', '=', 1),('unit','=','month')], limit=1)
        else:
            # Si es 1 mes (o contado), ¿debe tener recurrencia? 
            # El sistema original asume recurrencia si el producto es recurring_invoice.
            # Asumiremos la mensual por defecto si no se encuentra otra logica.
            recurrence_record = Recurrence.search([('duration', '=', 1),('unit','=','month')], limit=1)

        vals = {
            'term_number_id': term_number_id,
            'term_number': max_plazo,
            'payment_term_id': payment_term_id,
        }
        
        if recurrence_record:
            vals['recurrence_id'] = recurrence_record.id
            
        self.write(vals)

        # Llamar a funciones de suscripción del módulo extension
        try:
            self.onchange_end_date_suscrip()
        except Exception as e:
            _logger.warning("IRG onchange_end_date_suscrip failed: %s", str(e))

        try:
            self.create_subscription_schedule()
        except Exception as e:
            _logger.warning("IRG create_subscription_schedule failed: %s", str(e))

        _logger.info("=== IRG _auto_scheduled_order END for order %s ===", self.name)
