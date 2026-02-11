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
        discount_matricula_product = self.env['product.product'].search(
            [('default_code', '=', 'DESCUENTO_MATRICULA')], limit=1
        )
        if not discount_matricula_product:
            discount_matricula_product = self.env['product.product'].search(
                [('name', 'ilike', 'Descuento Matricula')], limit=1
            )
        if not discount_matricula_product:
            discount_matricula_product = self.env.ref(
                'irg_custom_discount.product_irg_discount', raise_if_not_found=False
            )
        
        if not financing_product:
            financing_product = self.env['product.product'].search([('default_code', '=', 'GASTOS_FIN')], limit=1)
            
        if not financing_product:
             # Fallback: ID proporcionado explícitamente
             financing_product = self.env['product.product'].browse(108)
             if not financing_product.exists():
                 financing_product = False

        # 1. Limpieza inicial: Eliminar líneas de financiación antiguas para recalcular
        if financing_product:
            financing_lines = self.order_line.filtered(lambda l: l.product_id == financing_product)
            if financing_lines:
                financing_lines.unlink()

        # Variable para almacenar la duración del curso si no hay atributos
        course_duration = 0

        for ol in self.order_line:
            # Ignoramos líneas de nota/sección o el propio producto de financiación
            if ol.display_type or (financing_product and ol.product_id == financing_product):
                continue
                
            if ol.product_id.recurring_invoice:
                
                # --- LÓGICA DE FINANCIACIÓN (NUEVO) ---
                # Buscamos si tiene atributo "Planes"
                ptav_plan = ol.product_id.product_template_attribute_value_ids.filtered(lambda x: x.attribute_id.name == 'Planes')
                
                if ptav_plan and financing_product:
                    # Asumimos un solo valor para planes
                    plan_value = ptav_plan[0]
                    
                    # Si NO es Contado, calculamos la diferencia
                    if 'contado' not in plan_value.name.lower():
                        _logger.info("Producto financiado detectado: %s - Plan: %s", ol.product_id.name, plan_value.name)
                        
                        # 1. Buscar la variante "Contado" hermana
                        # Debe tener el mismo template y los MISMOS otros atributos (excepto Planes)
                        other_attributes = ol.product_id.product_template_attribute_value_ids.filtered(lambda x: x.attribute_id.name != 'Planes')
                        
                        # Buscamos el valor "Contado" para el atributo Planes
                        # Primero obtenemos todos los valores posibles para ese atributo en este template
                        contado_value = plan_value.attribute_id.value_ids.filtered(lambda x: 'contado' in x.name.lower())
                        
                        if contado_value:
                            # Ahora buscamos el product.product que sea hermano
                            # Domain: Mismo Template + Atributo Contado + Otros Atributos
                            domain = [
                                ('product_tmpl_id', '=', ol.product_id.product_tmpl_id.id),
                                ('product_template_attribute_value_ids.product_attribute_value_id', 'in', contado_value.ids)
                            ]
                            
                            # Añadimos los otros atributos al dominio
                            for attr in other_attributes:
                                domain.append(('product_template_attribute_value_ids', 'in', attr.ids))
                                
                            sibling_contado = self.env['product.product'].search(domain, limit=1)
                            
                            if sibling_contado:
                                # Mark the main line so we can order the summary consistently
                                if ol.irg_line_type != 'master':
                                    ol.write({'irg_line_type': 'master'})
                                # === CÁLCULO DE FEE EN 3 NIVELES ===
                                # Nivel 1: Precios raw (use the actual order line price if present,
                                # otherwise fall back to variant lst_price = template.list_price + variant.price_extra)
                                raw_variant = ol.price_unit or ol.product_id.lst_price
                                raw_contado = sibling_contado.lst_price
                                _logger.info("IRG Financiación [RAW lst_price]: variant=%s, contado=%s, diff=%s",
                                             raw_variant, raw_contado, raw_variant - raw_contado)

                                # Nivel 2: Precios con pricelist
                                # Prefer the actual order line price (what the customer will pay)
                                # when available; otherwise try the pricelist price; finally
                                # fall back to the raw lst_price values.
                                pl_variant = ol.price_unit if (ol.price_unit and ol.price_unit > 0) else raw_variant
                                pl_contado = raw_contado
                                if self.pricelist_id:
                                    qty = ol.product_uom_qty or 1.0
                                    pv = self.pricelist_id._get_product_price(ol.product_id, qty)
                                    pc = self.pricelist_id._get_product_price(sibling_contado, qty)
                                    # If the line price wasn't provided, allow pricelist to set variant price
                                    if (not (ol.price_unit and ol.price_unit > 0)) and pv and pv > 0:
                                        pl_variant = pv
                                    if pc and pc > 0:
                                        pl_contado = pc
                                    _logger.info("IRG Financiación [PRICELIST '%s']: variant=%s, contado=%s, diff=%s",
                                                 self.pricelist_id.name, pl_variant, pl_contado, pl_variant - pl_contado)

                                # Nivel 3: price_extra directos del atributo Planes
                                plan_extra = ptav_plan[0].price_extra or 0.0
                                # Buscar el PTAV de Contado en el mismo template y atributo
                                contado_ptav = ol.product_id.product_tmpl_id.attribute_line_ids.filtered(
                                    lambda l: l.attribute_id.id == ptav_plan[0].attribute_id.id
                                ).product_template_value_ids.filtered(
                                    lambda v: 'contado' in (v.name or '').lower()
                                )
                                contado_extra = contado_ptav[0].price_extra if contado_ptav else 0.0
                                _logger.info("IRG Financiación [PRICE_EXTRA]: plan_extra=%s, contado_extra=%s, diff=%s",
                                             plan_extra, contado_extra, plan_extra - contado_extra)

                                # === DECIDIR FEE: primer nivel que dé diferencia > 0 ===
                                financing_fee_unit = pl_variant - pl_contado
                                fee_source = "PRICELIST"
                                if financing_fee_unit <= 0:
                                    financing_fee_unit = raw_variant - raw_contado
                                    fee_source = "RAW lst_price"
                                if financing_fee_unit <= 0:
                                    financing_fee_unit = plan_extra - contado_extra
                                    fee_source = "PRICE_EXTRA"

                                _logger.info("IRG Financiación FINAL: fee=%s (fuente: %s)",
                                             financing_fee_unit, fee_source)

                                if financing_fee_unit > 0:
                                    _logger.info("IRG Aplicando financiación. Diferencia unitaria: %s", financing_fee_unit)

                                    # Precio de contado para la línea del curso
                                    # Preferimos pricelist si da diferencia, sino raw
                                    if pl_variant - pl_contado > 0:
                                        contado_price = pl_contado
                                    elif raw_variant - raw_contado > 0:
                                        contado_price = raw_contado
                                    else:
                                        # Fee viene de price_extra: contado_price = precio actual - fee
                                        contado_price = pl_variant - financing_fee_unit

                                    # 2. Actualizar línea actual al precio de contado
                                    # y fijarlo para evitar que la pricelist lo sobrescriba después.
                                    ol.write({
                                        'price_unit': contado_price,
                                        'irg_force_price_unit': contado_price,
                                    })

                                    # 3. Crear línea de gastos de financiación (usar sudo para evitar problemas de permisos)
                                    _logger.info("IRG: about to create financing line for order %s (product %s), fee_unit=%s", self.name, financing_product.default_code or financing_product.id, financing_fee_unit)
                                    fin_line = self.env['sale.order.line'].sudo().create({
                                        'order_id': self.id,
                                        'product_id': financing_product.id,
                                        'name': f"Gastos de Financiación ({plan_value.name}) - {ol.product_id.name}",
                                        'product_uom_qty': ol.product_uom_qty,
                                        'price_unit': financing_fee_unit,
                                        'tax_id': [(6, 0, financing_product.taxes_id.ids)],
                                        'irg_line_type': 'financing',
                                        'irg_parent_line_id': ol.id,
                                    })
                                    if fin_line:
                                        _logger.info("IRG: created financing line %s (qty=%s, price_unit=%s) on order %s", fin_line.id, fin_line.product_uom_qty, fin_line.price_unit, self.name)
                                        try:
                                            # Post a message in order chatter so we can see the result from the backend/UI
                                            self.message_post(body=(f"IRG: Financing line created (id={fin_line.id}) - qty={fin_line.product_uom_qty}, unit_price={fin_line.price_unit} for order {self.name}"))
                                        except Exception as e:
                                            _logger.exception("IRG: failed to post message on order %s: %s", self.name, e)
                                    else:
                                        _logger.warning("IRG: failed to create financing line for order %s", self.name)

                                # Add Matricula + discount lines per master line (if products are available)
                                if matricula_product:
                                    existing_matricula_lines = self.order_line.filtered(
                                        lambda l: l.irg_parent_line_id == ol and l.irg_line_type in ['matricula', 'matricula_discount']
                                    )
                                    if existing_matricula_lines:
                                        existing_matricula_lines.unlink()

                                    qty = 1.0
                                    matricula_price = matricula_product.lst_price
                                    if self.pricelist_id:
                                        pl_price = self.pricelist_id._get_product_price(matricula_product, qty)
                                        if pl_price and pl_price > 0:
                                            matricula_price = pl_price

                                    matricula_line = self.env['sale.order.line'].sudo().create({
                                        'order_id': self.id,
                                        'product_id': matricula_product.id,
                                        'name': f"Matricula - {ol.product_id.name}",
                                        'product_uom_qty': qty,
                                        'price_unit': matricula_price,
                                        'tax_id': [(6, 0, matricula_product.taxes_id.ids)],
                                        'irg_force_price_unit': matricula_price,
                                        'irg_line_type': 'matricula',
                                        'irg_parent_line_id': ol.id,
                                    })
                                    if matricula_line and discount_matricula_product:
                                        discount_price = -(matricula_price * 0.5)
                                        self.env['sale.order.line'].sudo().create({
                                            'order_id': self.id,
                                            'product_id': discount_matricula_product.id,
                                            'name': f"Descuento Matricula - {ol.product_id.name}",
                                            'product_uom_qty': qty,
                                            'price_unit': discount_price,
                                            'tax_id': [(6, 0, discount_matricula_product.taxes_id.ids)],
                                            'irg_force_price_unit': discount_price,
                                            'irg_line_type': 'matricula_discount',
                                            'irg_parent_line_id': ol.id,
                                        })
                                        try:
                                            self.message_post(body=(f"IRG: failed to create financing line for order {self.name} (fee={financing_fee_unit})"))
                                        except Exception as e:
                                            _logger.exception("IRG: failed to post failure message on order %s: %s", self.name, e)
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
