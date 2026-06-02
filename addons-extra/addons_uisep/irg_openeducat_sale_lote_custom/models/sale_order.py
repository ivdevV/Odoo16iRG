# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_lot_id(self, course_id):
        # We are overriding the method to apply the specific logic requested
        # If the original method was smaller or split, we could call super(), 
        # but since the logic for constructing 'code' is monolithic, we rewrite it.
        
        # Retrieve line from context if available
        line_id = self.env.context.get('irg_get_lot_line_id')
        line = self.env['sale.order.line'].browse(line_id) if line_id else None
        
        _logger.info("IRG Custom Logic: get_lot_id called for course %s, extracted line %s from context", course_id.name, line)
        
        # Determine profix_01 (Category Code)
        # Priority: 
        # 1. From the Sale Order Line product (if found)
        # 2. From course_id.product_template_id
        # 3. From course_id.product_template_ids (first one)
        
        profix_01 = ''
        # Default fallback
        if course_id.product_template_id:
            profix_01 = course_id.product_template_id.categ_id.code or ''
        elif hasattr(course_id, 'product_template_ids') and course_id.product_template_ids:
            profix_01 = course_id.product_template_ids[0].categ_id.code or ''

        prefix_02 = 'GE'
        matching_line = line

        if matching_line:
            # Prefer the category code from the line's product
            if matching_line.product_id.categ_id.code:
                profix_01 = matching_line.product_id.categ_id.code
            
            if matching_line.product_id.product_template_attribute_value_ids:
                for ptav in matching_line.product_id.product_template_attribute_value_ids:
                    if ptav.attribute_id.name == 'Modalidad':
                        modalidad_name = ptav.product_attribute_value_id.name
                        _logger.info("IRG Custom Logic: Found Modalidad: %s", modalidad_name)
                        
                        if modalidad_name == 'Online':
                            prefix_02 = 'ONL'
                        elif modalidad_name == 'HomeClass':
                            prefix_02 = 'HC'
                        elif modalidad_name == 'Presencial':
                            prefix_02 = 'PRS'
                        else:
                            if ptav.code:
                                prefix_02 = ptav.code
                            else:
                                prefix_02 = modalidad_name[:3].upper() if modalidad_name else 'GE'
                        break
        else:
            for l in self.order_line:
                # Check if line matches the course
                is_match = False
                if hasattr(l.product_id, 'course_id') and l.product_id.course_id.id == course_id.id:
                    is_match = True
                elif course_id.product_template_id and l.product_id.product_tmpl_id.id == course_id.product_template_id.id:
                    is_match = True
                elif hasattr(course_id, 'product_template_ids') and l.product_id.product_tmpl_id.id in course_id.product_template_ids.ids:
                    is_match = True
                
                if is_match:
                    matching_line = l
                    # If we found the line, we prefer the category code from the line's product
                    if l.product_id.categ_id.code:
                        profix_01 = l.product_id.categ_id.code
                    
                    if l.product_id.product_template_attribute_value_ids:
                        for ptav in l.product_id.product_template_attribute_value_ids:
                            if ptav.attribute_id.name == 'Modalidad':
                                # Custom logic for Modalidad code
                                modalidad_name = ptav.product_attribute_value_id.name
                                _logger.info("IRG Custom Logic: Found Modalidad: %s", modalidad_name)
                                
                                if modalidad_name == 'Online':
                                    prefix_02 = 'ONL'
                                elif modalidad_name == 'HomeClass':
                                    prefix_02 = 'HC'
                                elif modalidad_name == 'Presencial':
                                    prefix_02 = 'PRS'
                                else:
                                    if ptav.code:
                                        prefix_02 = ptav.code
                                    else:
                                        prefix_02 = modalidad_name[:3].upper() if modalidad_name else 'GE'
                                break
                    break

        # Check if bonificado (price <= 0) - ONLY FOR ONL modality
        if matching_line and prefix_02 == 'ONL' and (matching_line.price_unit <= 0 or matching_line.price_subtotal <= 0):
            if profix_01.startswith('M'):
                profix_01 = 'MB'

        _logger.info("IRG Custom Logic: Determined prefix_02: %s", prefix_02)

        # Resolve date: prioritize matching_line.start_date_enroller, fallback to self.admission_date, fallback to today
        date = False
        if matching_line:
            date = matching_line.start_date_enroller
        if not date:
            date = self.admission_date
        if not date:
            date = fields.Date.today()

        _logger.info("IRG Custom Logic: Initial admission_date for batch calculation: %s", date)

        # Logic for date shift based on modality: HomeClass (HC) or Presencial (PRS)
        # We check against TODAY's day because admission_date is often set to the 1st of the month by the website.
        # We also ensure we only shift if the selected admission_date is actually in the current month.
        today = fields.Date.today()
        if prefix_02 in ['HC', 'PRS'] and today.day > 7 and date.month == today.month and date.year == today.year:
             date = date + relativedelta(months=1)
             _logger.info("IRG Custom Logic: Date shifted to next month (Current day %s > 7 and selected date is current month): %s", today.day, date)

        # HC Summer Period Rule: everything entering (or shifted to) between July and Sept 1st goes to September (09)
        if prefix_02 == 'HC' and date:
            if date.month in (7, 8) or (date.month == 9 and date.day == 1):
                date = date.replace(month=9, day=1)
                _logger.info("IRG Custom Logic: HC date forced to September 1st due to summer period: %s", date)

        year = date.strftime("%y")
        month = date.strftime("%m")

        prefix_04 = month
        prefix_05 = year
        # prefix_06 removed as requested
        # prefix_06 = {'es_MX': 'E', 'es_ES': 'E', 'pt_BR': 'P'}.get(course_id.lang, '')
        
        prefix_011 = course_id.code or ''       
        op_batch = self.env['op.batch']
        
        is_diplomado = False
        categ = matching_line.product_id.categ_id if matching_line else False
        if not categ and course_id.product_template_id:
            categ = course_id.product_template_id.categ_id
        if categ:
            if categ.code and (categ.code.upper().startswith('DI') or categ.code.upper() == 'D'):
                is_diplomado = True
            elif categ.name and 'DIPLOMADO' in categ.name.upper():
                is_diplomado = True
        
        if is_diplomado:
            profix_01 = 'DI'

        # Constructed code without prefix_06
        code = profix_01 + prefix_011 + prefix_02 +  prefix_05 + prefix_04
        
        _logger.info("IRG Custom Logic: Generated Code: %s", code)
        
        lot_id = op_batch.search([('code','=',code)])        
    
        if not lot_id:            
            ad = self.env['auto.admission.required'].search([], limit=1)        
            lot_values = {}
            if course_id.lang == 'pt_BR':     
                lot_values.update({
                    'tutor_id': ad.br_tutor_id.id if ad.br_tutor_id else False,
                    'professor_id': ad.br_professor_id.id if ad.br_professor_id else False,
                    'coordinator': ad.br_coordinator.id if ad.br_coordinator else False,
                    'teams_domain': ad.br_teams_domain if ad.br_teams_domain else False,
                    'teams_link': ad.br_teams_link if ad.br_teams_link else False,
                    'teams_msg': ad.br_teams_msg if ad.br_teams_msg else False,
                    'modality_id': ad.br_modality_id.id if ad.br_modality_id else False,
                })
            else:
                # Fallback por defecto (para es_MX, es_ES, o cualquier otro idioma como en_US en tests)
                lot_values.update({
                    'tutor_id': ad.mx_tutor_id.id if ad.mx_tutor_id else False,
                    'professor_id': ad.mx_professor_id.id if ad.mx_professor_id else False,
                    'coordinator': ad.mx_coordinator.id if ad.mx_coordinator else False,
                    'teams_domain': ad.mx_teams_domain if ad.mx_teams_domain else False,
                    'teams_link': ad.mx_teams_link if ad.mx_teams_link else False,
                    'teams_msg': ad.mx_teams_msg if ad.mx_teams_msg else False,
                    'modality_id': ad.mx_modality_id.id if ad.mx_modality_id else False,
                })
                
            if prefix_02 == 'HC':
                hc_mod = self.env['op.modality'].search([('name', '=ilike', 'HomeClass')], limit=1)
                if hc_mod:
                    lot_values['modality_id'] = hc_mod.id

            if prefix_02 in ['HC', 'PRS', 'ONL']:
                batch_start_date = date.replace(day=1)
            else:
                batch_start_date = date

            if prefix_02 in ('HC', 'ONL'):
                course_code = (course_id.code or '').strip().upper()
                duration_months = 24 if course_code == 'NC' else 16
                batch_end_date = batch_start_date + relativedelta(months=duration_months, days=-1)
                
                # Class start date
                if prefix_02 == 'HC':
                    date_start_class = batch_start_date + relativedelta(days=(4 - batch_start_date.weekday()) % 7)
                else:  # ONL
                    date_start_class = batch_start_date

                lot_values.update({
                    'name': code,
                    'code': code,
                    'course_id': course_id.id,
                    'start_date': batch_start_date,
                    'end_date': batch_end_date,
                    'date_start_class': date_start_class,
                })
            else:
                lot_values.update({
                    'name': code,
                    'code': code,
                    'course_id': course_id.id,
                    'start_date': batch_start_date,
                    'end_date': batch_start_date + relativedelta(years=1),
                })
            
            _logger.info("IRG Custom Logic: Creating new batch with values: %s", lot_values)
            
            lot_id = op_batch.create(lot_values)            
        else:
            _logger.info("IRG Custom Logic: Found existing batch: %s", lot_id.name)
            if not lot_id.tutor_id:
                ad = self.env['auto.admission.required'].search([], limit=1)
                if ad:
                    vals_to_write = {}
                    if course_id.lang == 'pt_BR':
                        vals_to_write.update({
                            'tutor_id': ad.br_tutor_id.id if ad.br_tutor_id else False,
                            'professor_id': ad.br_professor_id.id if ad.br_professor_id and not lot_id.professor_id else False,
                            'coordinator': ad.br_coordinator.id if ad.br_coordinator and not lot_id.coordinator else False,
                        })
                    else:
                        vals_to_write.update({
                            'tutor_id': ad.mx_tutor_id.id if ad.mx_tutor_id else False,
                            'professor_id': ad.mx_professor_id.id if ad.mx_professor_id and not lot_id.professor_id else False,
                            'coordinator': ad.mx_coordinator.id if ad.mx_coordinator and not lot_id.coordinator else False,
                        })
                    vals_to_write = {k: v for k, v in vals_to_write.items() if v}
                    if vals_to_write:
                        _logger.info("IRG Custom Logic: auto-completando tutor/profesor/coordinador del lote existente %s con: %s", lot_id.name, vals_to_write)
                        lot_id.write(vals_to_write)
            
        return lot_id
