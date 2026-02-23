# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class OpAdmission(models.Model):
    _inherit = 'op.admission'

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
                    configured_id = self.env['ir.config_parameter'].sudo().get_param(
                        'irg_elearning_correo_bienvenida_selector.online_template_id'
                    )
                    template = False
                    if configured_id and str(configured_id).isdigit():
                        template = self.env['mail.template'].sudo().browse(int(configured_id))
                        if not template.exists():
                            template = False
                    if not template:
                        template = self.env.ref(
                            'irg_elearning_correo_bienvenida_selector.email_op_admission_confirm_online',
                            raise_if_not_found=False,
                        )
                    if template:
                        template_id = template.id
            
            self.with_context(force_send=force).message_post_with_template(template_id, email_layout_xmlid=False)
            self.email_send_ok = True
