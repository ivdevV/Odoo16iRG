# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def _welcome_password_context(self):
        """Return context flags for password rendering in welcome templates.

        Rule:
        - First welcome mail for a student/user: show password as usual.
        - If a welcome mail was already sent before: only show password when
          we still have the same stored clear-text value; otherwise hide it.
        """
        self.ensure_one()

        user = self.student_id.user_id.sudo() if self.student_id and self.student_id.user_id else self.env['res.users']

        user_password_value = ''
        if user and user.exists() and 'new_password_user' in user._fields:
            user_password_value = user.new_password_user or ''

        prior_domain = [
            ('id', '!=', self.id),
            ('email_send_ok', '=', True),
        ]

        if user and user.exists():
            prior_domain.extend([
                '|',
                ('student_id.user_id', '=', user.id),
                ('email', '=', self.email),
            ])
        else:
            prior_domain.append(('email', '=', self.email))

        already_sent_before = bool(self.sudo().search_count(prior_domain))

        # First send => include password block.
        # Re-send/re-enrollment => include only if we can reuse same password.
        show_password = (not already_sent_before) or bool(user_password_value)

        return {
            'welcome_show_password': show_password,
            'welcome_password_value': user_password_value,
            'welcome_already_sent_before': already_sent_before,
        }

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
            is_online = False
            if self.batch_id.modality_id:
                modality_name = self.batch_id.modality_id.name.lower()
                if 'online' in modality_name:
                    is_online = True
            else:
                # Fallback based on batch code/name (only if modality is not explicitly set)
                if self.batch_id:
                    batch_code = (self.batch_id.code or '').upper()
                    batch_name = (self.batch_id.name or '').upper()
                    # Must contain 'ONL' and must NOT contain 'HC' (HomeClass) nor 'PRS' (Presencial)
                    if ('ONL' in batch_code or 'ONL' in batch_name) and not (
                        'HC' in batch_code or 'HC' in batch_name or
                        'PRS' in batch_code or 'PRS' in batch_name
                    ):
                        is_online = True

            if is_online:
                student_name = self.name
                if not self.tutor_id:
                    raise UserError('%s - El aplicante necesita un Tutor asignado.' % (student_name))
                if not self.batch_id.start_date:
                    raise UserError('%s - Necesita establecer fecha de inicio de Clases.' % (student_name))
                if not self.batch_id:
                    raise UserError('%s - Necesita asignar un grupo.' % (student_name))            

                # Safeguard: if date_start_class is empty in the batch, auto-populate it with start_date
                if self.batch_id and not self.batch_id.date_start_class and self.batch_id.start_date:
                    _logger.info("IRG Welcome Email: Auto-populating empty date_start_class with start_date %s for batch %s before sending email", self.batch_id.start_date, self.batch_id.name)
                    self.batch_id.sudo().write({'date_start_class': self.batch_id.start_date})

                template_id = self.env.ref('irg_elearning_correo_bienvenida_selector.email_op_admission_confirm_online').id
                template = self.env['mail.template'].sudo().browse(template_id)
                self._fix_welcome_password_placeholder(template)

                welcome_ctx = self._welcome_password_context()
                self.with_context(
                    force_send=force,
                    **welcome_ctx,
                ).message_post_with_template(template_id, email_layout_xmlid=False)
                self.email_send_ok = True
            else:
                return super(OpAdmission, self).send_mail(force)
        return True
