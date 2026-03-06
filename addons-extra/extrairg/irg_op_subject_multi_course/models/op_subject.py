from odoo import api, models


class OpSubject(models.Model):
    _inherit = "op.subject"

    course_ids = fields.Many2many(
        "op.course",
        string="Cursos",
        compute="_compute_course_ids",
        inverse="_inverse_course_ids",
        help="Courses linked to this subject. The first one is kept in Course for backward compatibility.",
    )

    def _apply_course_links(self, target_course_ids):
        Course = self.env["op.course"].sudo()
        for subject in self:
            current_courses = Course.search([("subject_ids", "in", subject.id)])
            target_courses = Course.browse(target_course_ids).exists()

            to_remove = current_courses - target_courses
            to_add = target_courses - current_courses

            if to_remove:
                to_remove.write({"subject_ids": [(3, subject.id)]})
            if to_add:
                to_add.write({"subject_ids": [(4, subject.id)]})

            subject.course_id = target_courses[:1].id or False

    @staticmethod
    def _m2m_commands_to_ids(current_ids, commands):
        ids = set(current_ids)

        if isinstance(commands, list) and commands and isinstance(commands[0], int):
            return list(set(commands))

        for command in commands or []:
            if not isinstance(command, (tuple, list)) or not command:
                continue

            op = command[0]
            if op == 6:
                ids = set(command[2] or [])
            elif op == 5:
                ids = set()
            elif op == 4:
                ids.add(command[1])
            elif op == 3:
                ids.discard(command[1])

        return list(ids)

    def _compute_course_ids(self):
        Course = self.env["op.course"].sudo()
        for subject in self:
            subject.course_ids = Course.search([("subject_ids", "in", subject.id)])

    def _inverse_course_ids(self):
        for subject in self:
            subject._apply_course_links(subject.course_ids.ids)

    @api.model_create_multi
    def create(self, vals_list):
        pending_courses = []
        for vals in vals_list:
            requested_courses = vals.pop("course_ids", False)
            pending_courses.append(requested_courses)
            if requested_courses and not vals.get("course_id"):
                resolved_ids = self._m2m_commands_to_ids([], requested_courses)
                vals["course_id"] = resolved_ids[:1] and resolved_ids[0] or False

        records = super().create(vals_list)

        for record, requested_courses in zip(records, pending_courses):
            if requested_courses:
                target_ids = self._m2m_commands_to_ids([], requested_courses)
                record._apply_course_links(target_ids)
        return records

    def write(self, vals):
        requested_courses = vals.pop("course_ids", False)

        if requested_courses:
            targets_per_subject = {
                subject.id: self._m2m_commands_to_ids(subject.course_ids.ids, requested_courses)
                for subject in self
            }

            if "course_id" not in vals and len(self) == 1:
                vals["course_id"] = targets_per_subject[self.id][:1] and targets_per_subject[self.id][0] or False

            result = super().write(vals)
            for subject in self:
                subject._apply_course_links(targets_per_subject[subject.id])
            return result

        return super().write(vals)
