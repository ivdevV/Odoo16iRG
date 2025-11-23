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
        
        _logger.info("IRG Custom Logic: get_lot_id called for course %s", course_id.name)
        
        date = self.admission_date
        _logger.info("IRG Custom Logic: Initial admission_date: %s", date)
        
        profix_01 = course_id.product_template_id.categ_id.code or ''
        prefix_02 = 'GE'

        for line in self.order_line:
            if (hasattr(line.product_id, 'course_id') and line.product_id.course_id.id == course_id.id) or \
            (line.product_id.product_tmpl_id.id == course_id.product_template_id.id):
                
                if line.product_id.product_template_attribute_value_ids:
                    for ptav in line.product_id.product_template_attribute_value_ids:
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
                                # Fallback to original logic or default if needed
                                if ptav.code:
                                    prefix_02 = ptav.code
                                else:
                                    prefix_02 = modalidad_name[:3].upper() if modalidad_name else 'GE'
                            break
                break

        _logger.info("IRG Custom Logic: Determined prefix_02: %s", prefix_02)

        # Logic for date shift based on modality: HomeClass (HC) or Presencial (PRS)
        # We check against TODAY's day because admission_date is often set to the 1st of the month by the website.
        # We also ensure we only shift if the selected admission_date is actually in the current month.
        today = fields.Date.today()
        if prefix_02 in ['HC', 'PRS'] and today.day > 7 and date.month == today.month and date.year == today.year:
             date = date + relativedelta(months=1)
             _logger.info("IRG Custom Logic: Date shifted to next month (Current day %s > 7 and selected date is current month): %s", today.day, date)

        year = date.strftime("%y")
        month = date.strftime("%m")

        prefix_04 = month
        prefix_05 = year
        # prefix_06 removed as requested
        # prefix_06 = {'es_MX': 'E', 'es_ES': 'E', 'pt_BR': 'P'}.get(course_id.lang, '')
        
        prefix_011 = course_id.code or ''       
        op_batch = self.env['op.batch']
        
        # Constructed code without prefix_06
        code = profix_01 + prefix_011 + prefix_02 +  prefix_05 + prefix_04
        
        _logger.info("IRG Custom Logic: Generated Code: %s", code)
        
        lot_id = op_batch.search([('code','=',code)])        
    
        if not lot_id:            
            ad = self.env['auto.admission.required'].search([], limit=1)        
            lot_values = {}
            if course_id.lang in ('es_MX', 'es_ES'):
                lot_values.update({
                    'tutor_id': ad.mx_tutor_id.id if ad.mx_tutor_id else False,
                    'professor_id': ad.mx_professor_id.id if ad.mx_professor_id else False,
                    'coordinator': ad.mx_coordinator.id if ad.mx_coordinator else False,
                    'teams_domain': ad.mx_teams_domain if ad.mx_teams_domain else False,
                    'teams_link': ad.mx_teams_link if ad.mx_teams_link else False,
                    'teams_msg': ad.mx_teams_msg if ad.mx_teams_msg else False,
                    'modality_id': ad.mx_modality_id.id if ad.mx_modality_id else False,
                })
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
                
            if prefix_02 in ['HC', 'PRS']:
                batch_start_date = date.replace(day=1)
            else:
                batch_start_date = date

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
            
        return lot_id
