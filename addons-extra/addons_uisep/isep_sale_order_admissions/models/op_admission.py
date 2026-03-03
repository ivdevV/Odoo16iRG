# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
from datetime import date


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


    def auto_enroll_student_auto(self):
        today = date.today()
        for record in self:
            if record.state != 'done' or not record.batch_id:
                continue

            for subject_batch in record.batch_id.subject_to_batch_ids:
                channel = subject_batch.subject_id.slide_channel_id
                if not channel:
                    continue

                existing = self.env['slide.channel.partner'].sudo().search([
                    ('partner_id', '=', record.partner_id.id),
                    ('channel_id', '=', channel.id),
                ], limit=1)

                in_range = (
                    (not subject_batch.date_from and not subject_batch.date_to) or
                    (subject_batch.date_from and subject_batch.date_from <= today and
                    (not subject_batch.date_to or today <= subject_batch.date_to))
                )

                vals = {
                    'active': True if in_range else False,
                    'course_id': record.course_id.id,
                    'register_id': record.register_id.id,
                    'admission_id': record.id,
                    'batch_id': record.batch_id.id,
                    'date_from': subject_batch.date_from,
                    'date_to': subject_batch.date_to,
                    'op_subject_id': subject_batch.subject_id.id,
                }

                if existing:
                    existing.write(vals)
                else:
                    vals.update({
                        'channel_id': channel.id,
                        'partner_id': record.partner_id.id,
                    })
                    new_cp = self.env['slide.channel.partner'].sudo().create(vals)



    def send_mail_view(self):
        self.send_mail(True)
        return True
        

    def send_mail(self, force):
        if not self.email_send_ok:           
            template_id = self.env.ref('isep_elearning_custom.email_op_admission_confirm').id
            template = self.env['mail.template'].sudo().browse(template_id)
            self._fix_welcome_password_placeholder(template)
            self.with_context(force_send=force).message_post_with_template(template_id, email_layout_xmlid=False)
            self.email_send_ok = True
        return True
