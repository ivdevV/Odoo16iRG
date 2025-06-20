import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'    

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for product in self.order_line:            

            if not product.product_template_id.course_type:
                raise UserError('Producto: %s \n\nRequerido "Modalidad": Especificar la modalidad del producto, contacte son el area de Contabilidad o Sistemas.' % (product.product_template_id.name) )
            #if product.product_template_id.course_type == 'classroom' and not product.admission_id:
            #    raise UserError('Producto: %s \n\nRequerido "Proceso de inscripción": Inscriba al estudiante en el curso comprado.\n1. Click en el boton inscrición del producto.\n2. Ingresa los datos minimos requeridos.\n 3. Guardar' % (product.product_template_id.name))
            
            """if product.product_template_id.course_type in ['classroom','online' ]:
                if self.partner_id.country_id:
                    raise UserError('Cliente: %s \n\nRequerido "Pais": Especificar el pais dentro de la informacion de contacto.' %  self.partner_id.name )

                elearning = self.env['slide.channel'].search([('product_template_id','=', product.product_template_id.id)], limit=1)
                if not elearning:
                    raise UserError('Producto: %s \n\nRequerido "Aperturar curso en Elearning (Campus)": Contacte con el departamento Academico.' % (product.product_template_id.name) )
                else:
                    self.env['slide.channel.partner'].create({
                        'partner_id': self.partner_id.id,
                        'channel_id': elearning.id,
                        'partner_email': self.partner_id.email,                        
                    })"""

        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'    
    """
    Enviar Solicitud de aplicacion desde Ventas.
    """
    admission_id = fields.Many2one('op.admission', string="Admisión" , copy=False) 
    elearning_id = fields.Many2one('slide.channel', string="eLearning" , copy=False) 
    elearning_partner_id = fields.Many2one('slide.channel.partner', string="eLearning Estudiante" , copy=False) 
    
    start_date_enroller = fields.Date(
        string='Fecha de inicio'
    )
    
    
    course_type = fields.Selection(
        string='Modalidad',
        related="product_id.course_type" ,
        selection=[('none', 'Ninguno'),('online', 'Online'), ('classroom', 'Online y Classroom')] ,
        )
    date_order = fields.Datetime(
        related="order_id.date_order",
        readonly=True,
        store=True,
        index=True,
    )
    account_analytic_id = fields.Many2one(
        related="order_id.analytic_account_id",
        readonly=True,
        store=True,
        index=True,
    )

    state_academic = fields.Selection(
        string='Estado de Solicitud',
        selection=[('waiting', 'En espera'),('process', 'En proceso'), ('done', 'Atendido')] ,
        tracking=True,
        default='waiting',
        copy=False
        )

    def state_academic_to_process(self):
        for self in self:
            self.state_academic = 'process'
    
    def state_academic_to_done(self):
        for self in self:
            self.state_academic = 'done'
    
    def state_academic_to_waiting(self):
        for self in self:
            self.state_academic = 'waiting'

    def elearning_add_user(self):
        for self in self:

            if self.course_type in ['classroom'] and not self.admission_id:
                    raise UserError('Primero debe generar la admision del Estudiante.' %  self.order_partner_id.name )                

            if self.course_type in ['classroom','online' ]:
                if not self.order_partner_id.country_id:
                    raise UserError('Cliente: %s \n\nRequerido "Pais": Especificar el pais dentro de la informacion de contacto.' %  self.order_partner_id.name )
                
                #elearning = self.env['slide.channel'].search([('product_template_id','=', product.product_template_id.id)], limit=1)
                #if not self.elearning_id:
                #    raise UserError('Producto: %s \n\nRequerido "Aperturar curso en Elearning (Campus)": Contacte con el departamento Academico.' % (self.product_template_id.name) )
                #else:                    
                #    self.env['slide.channel.partner'].search([('channel_id','=', self.elearning_id.id),('partner_id','=', self.partner_id.id)]).unlink()

                #    self.elearning_partner_id = self.env['slide.channel.partner'].create({
                #        'partner_id': self.order_partner_id.id,
                #        'channel_id': self.elearning_id.id,
                #        'partner_email': self.order_partner_id.email,
                #        'admission_id': self.admission_id.id,                        
                #   })



    def action_send_student(self):
        """op_admission = self.env['op.admission'].search([])
        action = self.env["ir.actions.actions"]._for_xml_id("openeducat_admission.view_op_admission_form")        
        # action['domain'] = [('id', 'in', op_admission.ids)]
        action['context'] = [()]
        action['context'] = {}
        action['target'] = 'new'
        action['flags'] = {'action_buttons': False}
        return action"""
        # raise UserError(str(self.order_partner_id.id))
        

        name = self.order_partner_id.name.replace('  ',' ').replace('   ',' ').replace('    ',' ').replace('     ',' ').replace('      ',' ').split(' ')
        
        first_name = ''
        middle_name = ''
        last_name = ''
        if len(name)==1:
            first_name=name[0]
        if len(name)>1:
            first_name = ''
            for i in range(0,len(name)-1):
                first_name+=str(name[i])+' '
            last_name = name[-1]
        
        
        return {
            #'name': self.order_id,
            'res_model': 'op.admission',
            'type': 'ir.actions.act_window',
            'context': {
                'default_first_name':first_name.strip(),
                'default_last_name':last_name.strip(),
                'default_sale_id':self.order_id.id,
                'default_email':self.order_id.partner_id.email,
                'default_mobile':self.order_id.partner_id.mobile,
                'default_phone':self.order_id.partner_id.phone,
                'default_product_template_id':self.product_template_id.id,
                'default_sale_line_id':self.id,
                'default_partner_id': self.order_partner_id.id
            },
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref("openeducat_admission.view_op_admission_form").id,
            'target': 'new'
        }
            
    def action_open_admission_id(self):
        return {
            #'name': self.order_id,
            'res_model': 'op.admission',
            'type': 'ir.actions.act_window',
            'res_id': self.admission_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref("openeducat_admission.view_op_admission_form").id,
            'target': 'target'
        }
        