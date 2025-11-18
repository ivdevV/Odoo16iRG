# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def get_lot_id(self, course_id):
        date = self.admission_date
        year = date.strftime("%y")
        month = date.strftime("%m")        
        profix_01 = course_id.product_template_id.categ_id.code or ''
        prefix_02 = 'GE'

        for line in self.order_line:
            if (hasattr(line.product_id, 'course_id') and line.product_id.course_id.id == course_id.id) or \
            (line.product_id.product_tmpl_id.id == course_id.product_template_id.id):
                
                if line.product_id.product_template_attribute_value_ids:
                    for ptav in line.product_id.product_template_attribute_value_ids:
                        if ptav.attribute_id.name == 'Modalidad':
                            if ptav.code:
                                prefix_02 = ptav.code
                            else:
                                prefix_02 = ptav.product_attribute_value_id.name[:3].upper() if ptav.product_attribute_value_id.name else 'GE'
                            break
                break

        prefix_04 = month
        prefix_05 = year
        prefix_06 = {'es_MX': 'E', 'es_ES': 'E', 'pt_BR': 'P'}.get(course_id.lang, '')
        prefix_011 = course_id.code or ''       
        op_batch = self.env['op.batch']
        code = profix_01 + prefix_011 + prefix_02 +  prefix_05 + prefix_04 + prefix_06        
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
                
            lot_values.update({
                'name': code,
                'code': code,
                'course_id': course_id.id,
                'end_date': fields.Date.today() + relativedelta(years=1),
            })            
            lot_id = op_batch.create(lot_values)            
        return lot_id
