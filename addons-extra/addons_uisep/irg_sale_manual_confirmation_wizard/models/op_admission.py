# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def send_mail(self, force):
        """Override del routing del modulo selector existente.

        Cuando manual_wizard_enabled = True:
        - Si batch.code contiene 'ONL'  -> plantilla online (configurable)
        - En cualquier otro caso       -> plantilla por defecto (configurable)
        - Si las plantillas no estan configuradas, cae a las xmlids historicas.

        Cuando manual_wizard_enabled = False: delega 100% en super().
        """
        ad = self.env['auto.admission.required'].search([], limit=1)
        if not ad or not ad.manual_wizard_enabled:
            return super().send_mail(force)

        if self.email_send_ok:
            return  # super delega aqui

        if not self.tutor_id and self.batch_id:
            tutor = False
            if ad:
                tutor = ad.br_tutor_id if self.course_id.lang == 'pt_BR' else ad.mx_tutor_id
            if not tutor:
                tutor = self.env.user
            if tutor:
                _logger.info("IRG Manual Wizard: auto-asignando tutor %s al lote %s para admisión %s", tutor.name, self.batch_id.name, self.name)
                self.batch_id.write({'tutor_id': tutor.id})

        student_name = self.name
        if not self.tutor_id:
            raise UserError(_('%s - El aplicante necesita un Tutor asignado.') % student_name)
        if not self.batch_id:
            raise UserError(_('%s - Necesita asignar un grupo.') % student_name)
        if not self.batch_id.start_date:
            raise UserError(_('%s - Necesita establecer fecha de inicio de Clases.') % student_name)

        batch_code = (self.batch_id.code or '').upper()
        is_online_batch = 'ONL' in batch_code

        # Determine if the admission's course is a diplomado
        categ_code = False
        if self.course_id:
            if self.course_id.product_template_id and self.course_id.product_template_id.categ_id:
                categ_code = self.course_id.product_template_id.categ_id.code
            elif hasattr(self.course_id, 'product_template_ids') and self.course_id.product_template_ids:
                first_pt = self.course_id.product_template_ids[0]
                if first_pt.categ_id:
                    categ_code = first_pt.categ_id.code

        if categ_code and categ_code.upper().startswith('DI'):
            is_online_batch = False

        template = False
        if is_online_batch:
            template = ad.welcome_template_online_id or self.env.ref(
                'irg_elearning_correo_bienvenida_selector.email_op_admission_confirm_online',
                raise_if_not_found=False,
            )
        if not template:
            template = ad.welcome_template_default_id or self.env.ref(
                'isep_elearning_custom.email_op_admission_confirm',
                raise_if_not_found=False,
            )
        if not template:
            _logger.warning("IRG Manual Wizard: ninguna plantilla resuelta, delegando en super()")
            return super().send_mail(force)

        _logger.info(
            "IRG Manual Wizard: enviando bienvenida admission=%s batch=%s online=%s template=%s",
            self.id, batch_code, is_online_batch, template.name,
        )

        if hasattr(self, '_fix_welcome_password_placeholder'):
            self._fix_welcome_password_placeholder(template)
        if hasattr(self, '_welcome_password_context'):
            welcome_ctx = self._welcome_password_context()
        else:
            welcome_ctx = {}

        self.with_context(
            force_send=force,
            **welcome_ctx,
        ).message_post_with_template(template.id, email_layout_xmlid=False)
        self.email_send_ok = True

    def submit_form(self):
        # Aseguramos que se guarde la fecha de nacimiento o un default
        birth = self.birth_date or '2000-01-01'
        res = super().submit_form()
        for record in self:
            if record.partner_id and not record.partner_id.birth_date:
                record.partner_id.write({'birth_date': birth})
        return res

    def _ensure_portal_user(self):
        """Asegura que el alumno tenga un usuario de portal (res.users) creado y vinculado.
        
        Si el alumno ya existe (student_id informado), pero no tiene usuario portal (user_id = False),
        este método busca un usuario existente por partner_id o por email/login, o crea uno nuevo
        con rol base.group_portal y lo vincula.
        """
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        for record in self:
            if not record.student_id:
                continue
            student = record.student_id
            partner = record.partner_id or student.partner_id
            if not partner:
                continue

            user = student.user_id
            
            # 1. Si no tiene usuario, buscar si ya existe para el partner
            if not user:
                user = self.env['res.users'].sudo().search([('partner_id', '=', partner.id)], limit=1)

            # 2. Si no, buscar por email/login
            if not user and (record.email or partner.email):
                email = (record.email or partner.email).strip()
                user = self.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                if user:
                    # Si el usuario ya existe, usamos su partner para mantener consistencia
                    partner = user.partner_id
                    if record.partner_id != partner:
                        record.sudo().write({'partner_id': partner.id})

            # 3. Si no existe en ningún sitio, crearlo vinculado al partner
            if not user:
                login_email = (record.email or partner.email or '').strip()
                if not login_email:
                    _logger.warning(
                        "IRG Manual Wizard: No se puede crear usuario de portal para admisión %s porque no tiene email.",
                        record.name
                    )
                    continue

                _logger.info(
                    "IRG Manual Wizard: Creando usuario portal para admisión %s, partner %s (%s)",
                    record.name, partner.name, login_email
                )
                user_vals = {
                    'name': partner.name,
                    'login': login_email,
                    'partner_id': partner.id,
                    'is_student': True,
                    'company_id': record.company_id.id or self.env.company.id,
                }
                if portal_group:
                    user_vals['groups_id'] = [(6, 0, [portal_group.id])]
                
                user = self.env['res.users'].sudo().create(user_vals)

            # 4. Vincular el usuario al estudiante y asegurar que coincide el partner
            student_vals = {}
            if student.user_id != user:
                student_vals['user_id'] = user.id
            if student.partner_id != partner:
                student_vals['partner_id'] = partner.id
            if student_vals:
                student.sudo().write(student_vals)

            # 5. Asegurar que tiene el grupo portal si no es usuario interno (base.group_user)
            if user and portal_group and portal_group not in user.groups_id:
                if not user.has_group('base.group_user'):
                    user.sudo().write({'groups_id': [(4, portal_group.id)]})

            # 6. Sincronizar datos básicos de contacto en el partner si faltan
            partner_vals = {}
            if not partner.email and (record.email or user.login):
                partner_vals['email'] = record.email or user.login
            if not partner.mobile and record.mobile:
                partner_vals['mobile'] = record.mobile
            if not partner.phone and record.phone:
                partner_vals['phone'] = record.phone
            if partner_vals:
                partner.sudo().write(partner_vals)

    def enroll_student(self):
        # Aseguramos que se cree y vincule el usuario de portal antes de procesar el registro
        self._ensure_portal_user()

        for record in self:
            if record.partner_id and not record.partner_id.birth_date:
                record.partner_id.write({'birth_date': record.birth_date or '2000-01-01'})
        
        # Guardar fechas de admisión originales para evitar que el super() las pise con la fecha de hoy
        saved_dates = {r.id: r.admission_date for r in self}
        
        res = super().enroll_student()
        
        for record in self:
            orig_date = saved_dates.get(record.id)
            if orig_date and record.admission_date != orig_date:
                _logger.info(
                    "IRG Manual Wizard: Restaurando admission_date a %s para la admisión %s (evitando sobreescritura de enroll_student)",
                    orig_date, record.name
                )
                record.admission_date = orig_date
        return res


    def get_student_vals(self):
        res = super().get_student_vals()
        if res and not res.get('birth_date'):
            res['birth_date'] = self.birth_date or self.partner_id.birth_date or '2000-01-01'
        return res

