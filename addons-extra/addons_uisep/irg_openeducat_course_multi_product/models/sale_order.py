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
                    _logger.info(f"DEBUG: Processing line {line.id}, Product: {line.product_template_id.name} ({line.product_template_id.id})")
                    # Updated search to find course where product is in product_template_ids
                    course_id = self.env['op.course'].search([('product_template_ids', 'in', [line.product_template_id.id])], limit=1)
                    _logger.info(f"DEBUG: Search by product_template_ids result: {course_id}")
                    
                    if not course_id:
                        # Fallback to old search if new field is empty (during migration/transition)
                        course_id = self.env['op.course'].search([('product_template_id', '=', line.product_template_id.id)], limit=1)
                        _logger.info(f"DEBUG: Search by product_template_id result: {course_id}")
                    
                    # Fallback to self.course_id if it matches the product
                    if not course_id and record.course_id:
                        _logger.info(f"DEBUG: Checking fallback record.course_id: {record.course_id.name} ({record.course_id.id})")
                        if record.course_id.product_template_id.id == line.product_template_id.id or line.product_template_id.id in record.course_id.product_template_ids.ids:
                            course_id = record.course_id
                            _logger.info("DEBUG: Fallback to record.course_id successful")
                        else:
                            _logger.info("DEBUG: Fallback to record.course_id FAILED - Product mismatch")

                    if course_id:
                        # We still set the single product_template_id on the order for backward compatibility 
                        # or we might need to decide which one to set if multiple lines. 
                        # The original logic seemed to pick the first one found.
                        record.product_template_id = line.product_template_id.id # Set the specific product from the line
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
            ('state', 'in', ['confirm', 'application', 'admission']),
            ('product_template_ids', 'in', [product_template_id.id]),
            ('period', '=', period)
        ], limit=1)

        # Fallback: buscar por product_template_id (campo antiguo)
        if not register_id:
            register_id = self.env['op.admission.register'].search([
                ('state', 'in', ['confirm', 'application', 'admission']),
                ('product_template_id', '=', product_template_id.id),
                ('period', '=', period)
            ], limit=1)

        # Fallback: buscar por course_id cuando product_template_ids no está sincronizado
        # (registros creados antes de instalar irg_openeducat_course_multi_product)
        if not register_id:
            course_for_search = self.env['op.course'].search(
                [('product_template_ids', 'in', [product_template_id.id])], limit=1
            )
            if not course_for_search:
                course_for_search = self.env['op.course'].search(
                    [('product_template_id', '=', product_template_id.id)], limit=1
                )
            if course_for_search:
                register_id = self.env['op.admission.register'].search([
                    ('state', 'in', ['confirm', 'application', 'admission']),
                    ('course_id', '=', course_for_search.id),
                    ('period', '=', period)
                ], limit=1)

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

            if course_id:
                end_date = self.gat_date_max_register(period)
                # Si el periodo ya venció, start_date no puede ser posterior a end_date
                start_date = min(fields.Date.today(), end_date)
                register_id = self.env['op.admission.register'].create({
                    'course_id': course_id.id,
                    'name': str(period) + ' ' + course_id.name,
                    'min_count': 1,
                    'max_count': 500,
                    'period': period,
                    'start_date': start_date,
                    'end_date': end_date,
                })
                register_id.start_application()
            else:
                msn = "No se encontro un Programa academico/Curso que este relacionado con el producto %s." % product_template_id.name
                self.error_admission_msn = msn if not self.error_admission_msn else self.error_admission_msn+'\n'+msn
                self.error_admission = True
                
        self.admission_register_id = register_id
