import logging
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_academic_product_template_id(self):
        for record in self:
            error_admission_msn = []
            # Filter lines that are academic programs and recurring invoices
            order_line = self.order_line.filtered(lambda x: x.product_template_id.is_academic_program and x.product_template_id.recurring_invoice )
            
            if order_line:
                for line in order_line:
                    # Updated search to find course where product is in product_template_ids
                    course_id = self.env['op.course'].search([('product_template_ids', 'in', [line.product_template_id.id])], limit=1)
                    
                    if course_id:
                        # We still set the single product_template_id on the order for backward compatibility 
                        # or we might need to decide which one to set if multiple lines. 
                        # The original logic seemed to pick the first one found.
                        record.product_template_id = line.product_template_id.id # Set the specific product from the line
                        record.course_id = course_id.id
                    else:
                        # Fallback to old search if new field is empty (during migration/transition)
                        course_id = self.env['op.course'].search([('product_template_id', '=', line.product_template_id.id)], limit=1)
                        if course_id:
                             record.product_template_id = course_id.product_template_id
                             record.course_id = course_id.id
                        else:
                            error_admission_msn.append("* El programa académico %s debe asociarse con el curso, comunicate con un asesor." % line.product_template_id.name)
            
            if error_admission_msn:
                record.error_admission_msn = '\n'.join(error_admission_msn)
                record.error_admission = True
            else:
                record.error_admission_msn = False
                record.error_admission = False

    def get_register_id(self, period, product_template_id):
        if not self.product_template_id or not self.course_id:
            self.get_academic_product_template_id()
            
        # Updated search for register
        register_id = self.env['op.admission.register'].search([
            ('state', 'in', ['confirm', 'application','admission']),
            ('product_template_ids', 'in', [product_template_id.id]),
            ('period','=', period )
        ], limit=1 )
        
        # Fallback to old search
        if not register_id:
             register_id = self.env['op.admission.register'].search([
                ('state', 'in', ['confirm', 'application','admission']),
                ('product_template_id', '=', product_template_id.id),
                ('period','=', period )
            ], limit=1 )

        if register_id:
            if register_id.state == 'confirm':
                register_id.start_application()            
                
        if not register_id:
            # Updated search for course
            course_id = self.env['op.course'].search([('product_template_ids', 'in', [product_template_id.id])], limit=1)
            
            # Fallback
            if not course_id:
                course_id = self.env['op.course'].search([('product_template_id', '=', product_template_id.id)], limit=1)

            # Fallback to self.course_id if it matches the product
            if not course_id and self.course_id:
                if self.course_id.product_template_id.id == product_template_id.id or product_template_id.id in self.course_id.product_template_ids.ids:
                    course_id = self.course_id

            _logger.info("\n###\n log 001 \n###")
            if course_id:
                register_id = self.env['op.admission.register'].create({
                    'course_id': course_id.id,
                    'name': str(period) +' '+course_id.name,
                    'min_count': 1,
                    'max_count':500,
                    'period': period,
                    'start_date':fields.Date.today(),
                    'end_date': self.gat_date_max_register(period),
                })
                register_id.start_application()
            else:
                msn = "No se encontro un Programa academico/Curso que este relacionado con el producto %s." % product_template_id.name
                self.error_admission_msn = msn if not self.error_admission_msn else self.error_admission_msn+'\n'+msn
                self.error_admission = True
                
        self.admission_register_id = register_id

    def get_lot_id(self, course_id):
        date = self.admission_date #datetime.now()
        year = date.strftime("%y")
        month = date.strftime("%m")
        
        # Updated to use product_template_ids
        # We take the category code from the first product found
        product = course_id.product_template_ids[:1]
        
        # Fallback to old field if new field is empty
        if not product:
            product = course_id.product_template_id

        profix_01 = product.categ_id.code or '' if product else ''
        
        prefix_02 = 'GE'
        #prefix_03 = 'IS'
        prefix_04 = month  #   Número del mes del año
        prefix_05 = year   #   últimos dígitos del año
        prefix_06 = {'es_MX': 'E', 'pt_BR': 'P'}.get(course_id.lang, '')     #   Digito del Idioma
        prefix_011 = course_id.code or ''
        
        
        # course_id.code+fields.Datetime.now().strftime('%Y%m%d%H%M%S')
        op_batch = self.env['op.batch']
        code = profix_01 + prefix_011 + prefix_02 +  prefix_04 + prefix_05 + prefix_06 #prefix_03 +
        
        lot_id = op_batch.search([('code','=',code)])
        
        
    
        if not lot_id:
            
            ad = self.env['auto.admission.required'].search([], limit=1)
        
            lot_values = {}
            if course_id.lang == 'es_MX':
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
