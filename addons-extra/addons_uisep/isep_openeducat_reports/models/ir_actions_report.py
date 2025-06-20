# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    certificado_web = fields.Boolean(string="Certificado Web")
    certificado_gratuito = fields.Boolean(string="Certificado Gratuito")
    list_price = fields.Float(string="Precio del Certificado", digits=(6,0))

    @api.constrains('list_price')
    def _check_list_price(self):
        for record in self:
            if not record.certificado_gratuito and record.list_price <= 0.0 :
                raise ValidationError("Se requiere establecer precio")


    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        report_sudo = self._get_report(report_ref)
        if 'disable_attachment' in self.env.context:
            attachment = report_sudo.attachment
            report_sudo.attachment= False
        res = super()._render_qweb_pdf_prepare_streams(report_ref = report_ref, data=data, res_ids = res_ids)
        if 'disable_attachment' in self.env.context:
            report_sudo.attachment = attachment
        return res

    def check_web_available(self, student_id, batch_id):
        self.ensure_one()
        if self.xml_id in ['isep_openeducat_reports.r_certificado1','isep_openeducat_reports.r_certificado5']:
           
           libreta = self.env['app.gradebook.student'].search([('student_id','=',student_id.id),('batch_id','=',batch_id.id)], limit=1)
           if not libreta or not libreta.state== 'closed' or  fields.Date.today <= student_id.file_closing_date:
               res = {'error_message': _('El certificado %s no puede generarse. Se requiere tener tus materias terminadas y solicitarse despues de la fecha de disertación.' %(self.display_name))
                  }
               return res
        if self.xml_id == 'isep_openeducat_reports.r_certificado4':
           libreta = self.env['app.gradebook.student'].search([('student_id','=',student_id.id),('batch_id','=',batch_id.id)], limit=1)
           if not libreta or not libreta.state== 'closed' :
               res = {'error_message': _('El certificado %s no puede generarse. Se requiere tener tus materias terminadas' %(self.display_name))
                  }
               return res

        if self.xml_id == 'isep_openeducat_reports.r_certificado6':
           #Carta no adeudo
            subscription_data = student_id.get_subscription_data()
            total_amount = subscription_data.get('t_amount_total_sale', 0)
            total_payment = subscription_data.get('t_amount_total_payment', 0)
            total_due = subscription_data.get('t_amount_recurring_due', 0)
            if total_amount > total_payment or total_due > 0 :
                res = {'error_message': _('El certificado %s no puede generarse. Se requieren tener tus pagos completos.' %(self.display_name))
                   }
                return res

        if self.xml_id == 'isep_openeducat_reports.r_certificado8':
            #Prácticas. 
            libreta = self.env['app.gradebook.student'].search([('student_id','=',student_id.id),('batch_id','=',batch_id.id)], limit=1)
            practice = self.env['practice.practice'].sudo().search([('op_student_id','=',student_id.id),('op_admission_id','=',libreta.admission_id.id)], limit=1)
            if not practice or (fields.Date.today() < practice.final_date) :
                res = {'error_message': _('El certificado %s no puede generarse. Se requiere solicitar después de tu fecha de finalización de prácticas.' %(self.display_name))
                    }
                return res


        return True
