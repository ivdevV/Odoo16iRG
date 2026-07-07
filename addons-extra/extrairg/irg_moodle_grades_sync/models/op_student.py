from odoo import models, api
from . import utils


class OpStudent(models.Model):
    _inherit = 'op.student'

    @api.model
    def _irg_match_moodle_student(self, moodle_user_id, fullname=None, email=None):
        """Resolve a Moodle user to an op.student.

        Chain (most to least reliable), stops at the first hit:
          1. irg.moodle.student.map  -> a previous manual resolution.
          2. res.partner.md_id == moodle_user_id  -> user already synced by the
             connector (the reliable link).
          3. partner email == moodle email (case-insensitive).
          4. normalized full name, only when the match is unique.

        Returns (student, method) where method is one of
        'manual' | 'md_id' | 'email' | 'name', or (empty recordset, None).
        """
        empty = self.browse()

        # 1. Manual resolution.
        if moodle_user_id:
            manual = self.env['irg.moodle.student.map'].search(
                [('moodle_user_id', '=', moodle_user_id)], limit=1)
            if manual:
                return manual.student_id, 'manual'

        # 2. Connector-synced partner (res.partner.md_id).
        if moodle_user_id:
            partner = self.env['res.partner'].search(
                [('md_id', '=', moodle_user_id)], limit=1)
            if partner:
                student = self.search([('partner_id', '=', partner.id)], limit=1)
                if student:
                    return student, 'md_id'

        # 3. Email match.
        if email:
            student = self.search(
                [('partner_id.email', '=ilike', email.strip())], limit=1)
            if student:
                return student, 'email'

        # 4. Normalized full name, unique only.
        if fullname:
            target = utils.normalize_name(fullname)
            if target:
                candidates = self.search([('name', '!=', False)])
                matches = candidates.filtered(
                    lambda s: utils.normalize_name(s.name) == target)
                if len(matches) == 1:
                    return matches, 'name'

        return empty, None
