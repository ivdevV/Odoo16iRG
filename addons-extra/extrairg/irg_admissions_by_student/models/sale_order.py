# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_admision_id(self, admission_register_id):
        """ Override provided by irg_admissions_by_student to support student_id """
        
        # Determine target partner (Student or Customer)
        target_partner = self.student_id or self.partner_id
        
        _logger.info(f"IRG_ADMISSIONS: Creating admission for order {self.name}. Target: {target_partner.name} (Student ID present: {bool(self.student_id)})")

        op_admission = self.env['op.admission']
        
        # Name splitting logic (as per original module)
        name = target_partner.name.replace('  ',' ').replace('   ',' ').replace('    ',' ').replace('     ',' ').replace('      ',' ').split(' ')
        
        first_name = '-'
        last_name = '-'
        if len(name)==1:
            first_name=name[0]
        if len(name)>1:
            first_name = ''
            for i in range(0,len(name)-1):
                first_name+=str(name[i])+' '
            last_name = name[-1]
            
        op_admission = op_admission.create({
            'name': target_partner.name,
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'sale_id': self.id,
            'email': target_partner.email,
            'mobile': target_partner.mobile,
            'phone': target_partner.phone,
            # 'product_template_id': self.product_template_id.id,
            'partner_id': target_partner.id, 
            'register_id' : admission_register_id.id,
            'course_id' : admission_register_id.course_id.id,
            'application_date': fields.Datetime.now(),
            'admission_date': fields.Datetime.now(),
            'fees_term_id': self.env['op.fees.terms'].search([], limit=1).id,
            'gender': self.gender or target_partner.gender or 'o',
            'batch_id': self.get_lot_id(admission_register_id.course_id).id,
            'order_id': self.id,    
        })
        
        self.admission_id = op_admission.id


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    student_id = fields.Many2one(related='order_id.student_id', string='Alumno', store=True, readonly=True)

    def action_send_student(self):
        """ Override action to open admission form with correct student context """
        res = super(SaleOrderLine, self).action_send_student()
        
        if self.order_id.student_id:
            target_partner = self.order_id.student_id
            
            # Robust name splitting
            clean_name = " ".join(target_partner.name.split())
            name_parts = clean_name.split(" ")
            
            first_name = ""
            last_name = ""
            if len(name_parts) == 1:
                first_name = name_parts[0]
            elif len(name_parts) > 1:
                first_name = " ".join(name_parts[:-1])
                last_name = name_parts[-1]

            if isinstance(res, dict) and 'context' in res:
                # Ensure context is a clean dict we can modify
                if not isinstance(res['context'], dict):
                     res['context'] = {} # Fallback, though usually it's a dict
                
                # Force the student details into the default context
                res['context'].update({
                    'default_first_name': first_name.strip(),
                    'default_last_name': last_name.strip(),
                    'default_partner_id': target_partner.id,
                    'default_email': target_partner.email,
                    'default_mobile': target_partner.mobile,
                    'default_phone': target_partner.phone,
                })
        return res
