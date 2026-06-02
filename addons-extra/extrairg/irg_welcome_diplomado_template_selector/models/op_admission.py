# -*- coding: utf-8 -*-

import logging

from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def _irg_welcome_batch_code(self):
        self.ensure_one()
        return (self.batch_id.code or '').strip().upper() if self.batch_id else ''

    def _irg_welcome_category_codes(self):
        self.ensure_one()
        codes = []
        course = self.course_id
        if not course:
            return codes

        templates = course.product_template_id
        if 'product_template_ids' in course._fields:
            templates |= course.product_template_ids

        for template in templates:
            code = template.categ_id.code
            if code:
                codes.append(code.strip().upper())
        return codes

    def _irg_is_diplomado_welcome(self):
        self.ensure_one()
        batch_code = self._irg_welcome_batch_code()
        return batch_code.startswith('DI') or any(
            code.startswith('DI') for code in self._irg_welcome_category_codes()
        )

    def _irg_diplomado_welcome_template(self, ad):
        template = ad.welcome_template_diplomado_id if ad else False
        return template or self.env.ref(
            'irg_welcome_diplomado_template_selector.email_op_admission_confirm_diplomado',
            raise_if_not_found=False,
        ) or self.env.ref(
            'isep_elearning_custom.email_op_admission_confirm',
            raise_if_not_found=False,
        )

    def _irg_resolve_welcome_template(self, ad):
        self.ensure_one()
        batch_code = self._irg_welcome_batch_code()

        if self._irg_is_diplomado_welcome():
            return self._irg_diplomado_welcome_template(ad), 'diplomado'

        if 'ONL' in batch_code:
            template = ad.welcome_template_online_id or self.env.ref(
                'irg_elearning_correo_bienvenida_selector.email_op_admission_confirm_online',
                raise_if_not_found=False,
            )
            if template:
                return template, 'online'

        template = ad.welcome_template_default_id or self.env.ref(
            'isep_elearning_custom.email_op_admission_confirm',
            raise_if_not_found=False,
        )
        return template, 'default'

    def send_mail(self, force):
        ad = self.env['auto.admission.required'].search([], limit=1)
        if not ad or not ad.manual_wizard_enabled:
            return super().send_mail(force)

        if self.email_send_ok:
            return True

        if not self.tutor_id and self.batch_id:
            tutor = False
            if ad:
                tutor = ad.br_tutor_id if self.course_id.lang == 'pt_BR' else ad.mx_tutor_id
            if not tutor:
                tutor = self.env.user
            if tutor:
                _logger.info(
                    'IRG Diplomado Welcome: auto-asignando tutor %s al lote %s para admision %s',
                    tutor.name,
                    self.batch_id.name,
                    self.name,
                )
                self.batch_id.write({'tutor_id': tutor.id})

        student_name = self.name
        if not self.tutor_id:
            raise UserError(_('%s - El aplicante necesita un Tutor asignado.') % student_name)
        if not self.batch_id:
            raise UserError(_('%s - Necesita asignar un grupo.') % student_name)
        if not self.batch_id.start_date:
            raise UserError(_('%s - Necesita establecer fecha de inicio de Clases.') % student_name)

        template, route = self._irg_resolve_welcome_template(ad)
        if not template:
            _logger.warning('IRG Diplomado Welcome: ninguna plantilla resuelta, delegando en super()')
            return super().send_mail(force)

        _logger.info(
            'IRG Diplomado Welcome: enviando bienvenida admission=%s batch=%s route=%s template=%s',
            self.id,
            self._irg_welcome_batch_code(),
            route,
            template.name,
        )

        if hasattr(self, '_fix_welcome_password_placeholder'):
            self._fix_welcome_password_placeholder(template)
        welcome_ctx = self._welcome_password_context() if hasattr(self, '_welcome_password_context') else {}

        self.with_context(
            force_send=force,
            **welcome_ctx,
        ).message_post_with_template(template.id, email_layout_xmlid=False)
        self.email_send_ok = True
        return True
