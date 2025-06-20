# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta

class IrAttachment(models.Model):
    _inherit = ['ir.attachment']
    _name = 'ir.attachment'

    sign_certificate_id = fields.Many2one('account.move', string="Sign Certificate")
    cert_invoice_id = fields.Many2one('account.move', string="Factura del Certificado")
    certificado_web = fields.Boolean(string="Certificado Web")
    certificado_gratuito = fields.Boolean(string="Certificado Gratuito")


    def validate_access(self, access_token):
        # Check if is certificate
        if self.sudo().certificado_web:
            # Check if student and user 
            student_id = self.env['op.student'].sudo().search([('user_id','=',self.env.user.id)], limit=1)
            if self.env.is_superuser() or (self.sudo().res_id == student_id.id and self.sudo().res_model == 'op.student'):
                if self.sudo().certificado_gratuito:
                    return self.sudo()
                if self.sudo().cert_invoice_id and self.sudo().cert_invoice_id.payment_state == 'paid':
                    return self.sudo()
            
        res = super().validate_access(access_token)
        return res

    def remove_certificates(self):
       
        try:
           cert_days_fpayment = int(self.env["ir.config_parameter"].sudo().get_param("cert_days_fpayment"))
        except ValueError:
           cert_days_fpayment = 7
        try:
           cert_days_fdownload = int(self.env["ir.config_parameter"].sudo().get_param("cert_days_fdownload"))
        except ValueError:
           cert_days_fdownload = 3

        certificados = self.search([('certificado_web','=',True)])
        certificados_vencidos_cfactura = certificados.filtered(lambda c: c.cert_invoice_id and c.cert_invoice_id.payment_state != 'paid' and ((c.create_date + timedelta(days=cert_days_fpayment))  < fields.Datetime.now()))
        certificados_vencidos_cfactura.unlink()

        certificados = self.search([('certificado_web','=',True)])
        certificados_vencidos_pagados = certificados.filtered(lambda c: c.cert_invoice_id and c.cert_invoice_id.payment_state == 'paid' and ((c.cert_invoice_id.get_last_payment_date() + timedelta(days=cert_days_fdownload))  < fields.Date.today()))
        certificados_vencidos_pagados.unlink()

        certificados = self.search([('certificado_web','=',True),('certificado_gratuito','=',True)])
        certificados_vencidos_gratuitos = certificados.filtered(lambda c: (c.create_date + timedelta(days=cert_days_fpayment))  < fields.Datetime.now())
        certificados_vencidos_gratuitos.unlink()

        return
