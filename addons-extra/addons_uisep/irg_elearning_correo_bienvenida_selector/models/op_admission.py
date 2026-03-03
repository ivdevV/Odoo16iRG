# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def _fix_welcome_password_placeholder(self, template):
        body_html = template.body_html or ''
        replacements = (
            ('user.new_password_user', 'object.new_password_user'),
            ('{{ user.new_password_user }}', '{{ object.new_password_user }}'),
            ('${user.new_password_user}', '${object.new_password_user}'),
        )
        new_body = body_html
        for old_value, new_value in replacements:
            new_body = new_body.replace(old_value, new_value)
        if new_body != body_html:
            template.sudo().write({'body_html': new_body})

    def send_mail(self, force):
        if not self.email_send_ok:
            student_name = self.name
            if not self.tutor_id:
                raise UserError('%s - El aplicante necesita un Tutor asignado.' % (student_name))
            if not self.batch_id.start_date:
                raise UserError('%s - Necesita establecer fecha de inicio de Clases.' % (student_name))
            if not self.batch_id:
                raise UserError('%s - Necesita asignar un grupo.' % (student_name))            
            
            # Lógica para seleccionar la plantilla según la modalidad
            template_id = self.env.ref('isep_elearning_custom.email_op_admission_confirm').id
            
            if self.batch_id.modality_id:
                modality_name = self.batch_id.modality_id.name.lower()
                if 'online' in modality_name:
                    template_id = self.env.ref('irg_elearning_correo_bienvenida_selector.email_op_admission_confirm_online').id

            template = self.env['mail.template'].sudo().browse(template_id)
            self._fix_welcome_password_placeholder(template)
            
            self.with_context(force_send=force).message_post_with_template(template_id, email_layout_xmlid=False)
            self.email_send_ok = True
