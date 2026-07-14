# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import html_escape


class OpStudent(models.Model):
    _inherit = "op.student"

    irg_campus_blocked = fields.Boolean(
        string="Campus bloqueado",
        compute="_compute_irg_campus_blocked",
    )

    @api.depends("user_id", "user_id.active")
    def _compute_irg_campus_blocked(self):
        for student in self:
            user = student.with_context(active_test=False).user_id
            student.irg_campus_blocked = bool(user) and not user.active

    def action_block_campus_access(self):
        return self._irg_set_campus_access(active=False)

    def action_unblock_campus_access(self):
        return self._irg_set_campus_access(active=True)

    def _irg_set_campus_access(self, active):
        if not self.env.user.has_group(
            "openeducat_core.group_op_back_office_admin"
        ):
            raise AccessError(_("No tiene permisos para cambiar el acceso al campus."))

        targets = []
        for student in self:
            linked_user_id = student.with_context(active_test=False).user_id.id
            if not linked_user_id:
                raise UserError(_("El alumno no tiene un usuario portal vinculado."))

            target_user = (
                self.env["res.users"]
                .with_context(active_test=False)
                .browse(linked_user_id)
                .exists()
            )
            if not target_user:
                raise UserError(_("El usuario portal vinculado ya no existe."))
            if (
                not target_user.has_group("base.group_portal")
                or target_user.has_group("base.group_user")
            ):
                raise UserError(
                    _("El usuario vinculado no es un usuario portal externo válido.")
                )
            targets.append((student, target_user))

        for student, target_user in targets:
            if target_user.active == active:
                continue

            target_user.sudo().write({"active": active})
            if active:
                body = _(
                    "Acceso autenticado a Odoo desbloqueado por %(operator)s "
                    "para el usuario portal %(target)s.",
                    operator=html_escape(self.env.user.name),
                    target=html_escape(target_user.name),
                )
            else:
                body = _(
                    "Acceso autenticado a Odoo bloqueado por %(operator)s "
                    "para el usuario portal %(target)s.",
                    operator=html_escape(self.env.user.name),
                    target=html_escape(target_user.name),
                )
            student.message_post(body=body)

        return False
