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
        
        # Fallback 1: Código interno
        if not financing_product:
            financing_product = self.env['product.product'].search([('default_code', '=', 'GASTOS_FIN')], limit=1)
            
        # Fallback 2: ID explícita
        if not financing_product:
             financing_product = self.env['product.product'].browse(108)
             if not financing_product.exists():
                 financing_product = False

        if not financing_product:
            _logger.error("IRG Financing: Product NOT FOUND.")

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
                
                # --- LÓGICA DE FINANCIACIÓN (MEJORADA) ---
                try:
                    # Buscamos si tiene atributo "Planes" (Case insensitive)
                    ptavs = ol.product_id.product_template_attribute_value_ids
                    ptav_plan = ptavs.filtered(lambda x: x.attribute_id.name.lower() == 'planes')
                    
                    if ptav_plan and financing_product:
                        # Asumimos un solo valor para planes
                        plan_value = ptav_plan[0]
                        
                        # Si NO es Contado, calculamos la diferencia
                        if 'contado' not in plan_value.name.lower():
                            _logger.info("IRG Financing: Producto financiado detectado: %s - Plan: %s", ol.product_id.name, plan_value.name)
                            
                            # 1. Buscar el valor de atributo "Contado" (PAV)
                            contado_pav = plan_value.attribute_id.value_ids.filtered(lambda x: 'contado' in x.name.lower())
                            
                            if contado_pav:
                                # 2. Buscar el PTAV correspondiente en este template
                                contado_ptav = self.env['product.template.attribute.value'].search([
                                    ('product_tmpl_id', '=', ol.product_id.product_tmpl_id.id),
                                    ('product_attribute_value_id', 'in', contado_pav.ids)
                                ], limit=1)
                                
                                if contado_ptav:
                                    # 3. Construir dominio para buscar el hermano
                                    # Debe tener contado_ptav Y conservar los otros atributos
                                    other_ptavs = ptavs.filtered(lambda x: x.attribute_id.name.lower() != 'planes')
                                    
                                    domain = [
                                        ('product_tmpl_id', '=', ol.product_id.product_tmpl_id.id),
                                        ('product_template_attribute_value_ids', 'in', contado_ptav.ids)
                                    ]
                                    
                                    for ptav in other_ptavs:
                                        domain.append(('product_template_attribute_value_ids', 'in', ptav.ids))
                                        
                                    sibling_contado = self.env['product.product'].search(domain, limit=1)
                                    
                                    if sibling_contado:
                                        # Calcular diferencia
                                        current_price = ol.price_unit
                                        
                                        # Obtener precio usando la tarifa si existe
                                        if self.pricelist_id:
                                            # Asegurar contexto limpio de variantes forzadas
                                            contado_price = sibling_contado.with_context(
                                                pricelist=self.pricelist_id.id, 
                                                uom=ol.product_uom.id
                                            ).price
                                        else:
                                            contado_price = sibling_contado.lst_price

                                        financing_fee_unit = current_price - contado_price
                                        
                                        if financing_fee_unit > 0:
                                            _logger.info("IRG Financing: Aplicando financiación. Diferencia unitaria: %s", financing_fee_unit)
                                            
                                            # 2. Actualizar línea actual al precio de contado
                                            ol.write({'price_unit': contado_price})
                                            
                                            # 3. Crear línea de gastos de financiación
                                            # Usamos la misma cantidad que la línea original
                                            self.env['sale.order.line'].create({
                                                'order_id': self.id,
                                                'product_id': financing_product.id,
                                                'name': f"Gastos de Financiación ({plan_value.name}) - {ol.product_id.name}",
                                                'product_uom_qty': ol.product_uom_qty,
                                                'price_unit': financing_fee_unit,
                                                'tax_id': [(6, 0, financing_product.taxes_id.ids)],
                                            })
                                    else:
                                        _logger.warning("IRG Financing: No se encontró variante Contado hermana para %s", ol.product_id.name)
                                else:
                                    _logger.warning("IRG Financing: No se encontró PTAV Contado para el template")
                            else:
                                _logger.warning("IRG Financing: No se encontró valor de atributo Contado")
                except Exception as e:
                    _logger.error("IRG Financing: Error crítico en cálculo de financiación: %s", str(e))

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
