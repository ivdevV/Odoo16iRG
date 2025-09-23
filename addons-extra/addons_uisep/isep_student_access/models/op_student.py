# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, _


class OpStudent(models.Model):
    _inherit = 'op.student'

    login_date = fields.Datetime(related='user_id.login_date', string='Última autenticación')
    login_line_ids = fields.One2many('op.login.lines', 'student_id', string='Login Lines')

class OpLoginLines(models.Model):
    _name = 'op.login.lines'
    _description = 'Login Lines'
    _order = 'id desc'

    student_id = fields.Many2one('op.student', string='Student', required=True)
    login_date = fields.Datetime(string='Login Date', required=True)

    last_access = fields.Char(string='Ago', readonly=True,
                              compute='_get_last_access')

    def _get_last_access(self):
        for record in self:
            access_ago = fields.Datetime.now() - record.login_date
            total_seconds = int(access_ago.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            hours, minutes = divmod(minutes, 60)
            
            parts = []
            if access_ago.days > 0:
                if access_ago.days > 365:
                    years, days = divmod(access_ago.days, 365)
                    parts.extend(["{} años".format(years), "{} días".format(days)])
                else:
                    parts.append("{} días".format(access_ago.days))
            if hours > 0:
                parts.append("{} horas".format(hours))
            if minutes > 0:
                parts.append("{} minutos".format(minutes))
            
            record.last_access = ", ".join(parts) if parts else "0 minutos"


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    def _update_last_login(self):
        result = super(ResUsers, self)._update_last_login()

        student = self.env['op.student'].sudo().search([('user_id', '=', self.id)], limit=1)
        if student:
            self.env['op.login.lines'].sudo().create({
                'student_id': student.id,
                'login_date': fields.Datetime.now()
            })
        return result