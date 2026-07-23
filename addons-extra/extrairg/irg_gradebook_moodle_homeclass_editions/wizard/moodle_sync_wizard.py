from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.irg_gradebook_moodle_routing.models.moodle_routing import (
    COURSE_MAP_CONTEXT_KEY,
)


class IrgGradebookMoodleSyncWizard(models.TransientModel):
    _inherit = "irg.gradebook.moodle.sync.wizard"

    def _irg_homeclass_candidates(self):
        """Return active HomeClass maps only for an unambiguous HC batch."""
        self.ensure_one()
        batch = self.gradebook_student_id.batch_id
        batch_code = (batch.code or "").upper()
        if "HC" not in batch_code or "ONL" in batch_code:
            return self.env["irg.gradebook.moodle.course.map"]
        return self.env["irg.gradebook.moodle.course.map"].search(
            [
                ("op_course_id", "=", self.gradebook_student_id.course_id.id),
                ("modality", "=", "homeclass"),
                ("active", "=", True),
            ]
        )

    def _irg_order_homeclass_candidates(self, candidates):
        """Prioritize batch edition, generic maps, then Moodle course ID."""
        self.ensure_one()
        batch = self.gradebook_student_id.batch_id
        edition_year = batch.start_date.year if batch.start_date else False
        key = lambda mapping: (mapping.moodle_course_id, mapping.id)
        exact = candidates.filtered(
            lambda mapping: edition_year
            and mapping.edition_year == edition_year
        ).sorted(key=key)
        generic = candidates.filtered(
            lambda mapping: not mapping.edition_year
        ).sorted(key=key)
        remaining = (candidates - exact - generic).sorted(key=key)
        return candidates.browse(exact.ids + generic.ids + remaining.ids)

    @staticmethod
    def _irg_resolution_conflict(entry, map_lines):
        """Return structural Activity-ID conflicts, never absent activities."""
        items = entry.get("gradeitems", [])
        item_usage = {}
        for map_line in map_lines:
            matches = [
                (index, item)
                for index, item in enumerate(items)
                if item.get("id") == map_line.moodle_activity_id
                or item.get("cmid") == map_line.moodle_activity_id
            ]
            if len(matches) > 1:
                return _(
                    "La actividad Moodle %s tiene una resolución ambigua "
                    "(%s coincidencias por id/cmid)."
                ) % (map_line.moodle_activity_id, len(matches))
            if not matches:
                continue
            item_index, item = matches[0]
            if item.get("itemmodule") != map_line.activity_type:
                return _(
                    "La actividad Moodle %s no coincide con el tipo "
                    "mapeado (%s)."
                ) % (map_line.moodle_activity_id, map_line.activity_type)
            if item_index in item_usage:
                return _(
                    "La actividad Moodle %s tiene una resolución ambigua: "
                    "el mismo grade item se reutiliza."
                ) % map_line.moodle_activity_id
            item_usage[item_index] = map_line
        return False

    def _irg_load_multiple_homeclass(self, candidates):
        """Load one valid Moodle result per subject across HC editions."""
        self.ensure_one()
        self._check_moodle_sync_access()
        candidates = self._irg_order_homeclass_candidates(candidates)
        self.line_ids.unlink()

        map_model = self.env["irg.gradebook.moodle.map"]
        for course_map in candidates:
            course_subject_maps = map_model.with_context(
                **{COURSE_MAP_CONTEXT_KEY: course_map.id}
            ).search([("active", "=", True)])
            integrity_error = course_subject_maps._irg_parent_integrity_error()
            if integrity_error:
                raise UserError(
                    _("El routing Moodle contiene un mapa incoherente: %s")
                    % integrity_error
                )

        service = self._get_service()
        gradebook_student = self.gradebook_student_id
        scale = gradebook_student.gradebook_id.grading_scale or 10.0
        line_model = self.env["irg.gradebook.moodle.sync.wizard.line"]
        result_model = self.env["app.gradebook.result"]
        course_cache = {}
        methods = set()

        for gradebook_subject in gradebook_student.gradebook_subject_ids:
            subject = gradebook_subject.op_subject_id
            base_values = {
                "wizard_id": self.id,
                "gradebook_subject_id": gradebook_subject.id,
                "subject_id": subject.id,
            }
            attempts = []
            for course_map in candidates:
                subject_maps = map_model.with_context(
                    **{COURSE_MAP_CONTEXT_KEY: course_map.id}
                ).search(
                    [
                        ("op_subject_id", "=", subject.id),
                        ("active", "=", True),
                    ]
                )
                prefix = _("Curso Moodle %s") % course_map.moodle_course_id
                if not subject_maps:
                    attempts.append(_("%s: sin mapeo de asignatura.") % prefix)
                    continue
                if len(subject_maps) > 1:
                    line_model.create(
                        dict(
                            base_values,
                            state="incompatible",
                            apply_line=False,
                            moodle_info=_(
                                "%s: más de un mapa activo para la "
                                "asignatura."
                            )
                            % prefix,
                        )
                    )
                    break

                subject_map = subject_maps
                if not subject_map.line_ids:
                    attempts.append(_("%s: sin actividades mapeadas.") % prefix)
                    continue
                course_id = subject_map.moodle_course_id
                if course_id not in course_cache:
                    course_cache[course_id] = service.get_user_grade_items(
                        course_id
                    )
                usergrades, emails = course_cache[course_id]
                entry, method = self._find_student_entry(
                    gradebook_student.partner_id,
                    gradebook_student.student_id.name,
                    usergrades,
                    emails,
                )
                if entry is None:
                    attempts.append(_("%s: alumno no encontrado.") % prefix)
                    continue

                resolution_conflict = self._irg_resolution_conflict(
                    entry, subject_map.line_ids
                )
                if resolution_conflict:
                    line_model.create(
                        dict(
                            base_values,
                            state="incompatible",
                            apply_line=False,
                            moodle_info=resolution_conflict,
                        )
                    )
                    break

                grades_by_type = self._grades_by_type(
                    entry, subject_map.line_ids, scale
                )
                valid_lines = []
                reasons = []
                compatibility_conflict = False
                for result_type in sorted(grades_by_type):
                    data = grades_by_type[result_type]
                    compatibility_reason = self._compatibility_reason(
                        gradebook_subject, result_type
                    )
                    if compatibility_reason:
                        compatibility_conflict = compatibility_reason
                        break
                    if data["error"]:
                        reasons.append(data["error"])
                        continue
                    if data["avg"] is None:
                        reasons.append(
                            _("No hay una nota utilizable para %s.")
                            % result_type
                        )
                        continue
                    current = result_model.search(
                        [
                            (
                                "gradebook_subject_id",
                                "=",
                                gradebook_subject.id,
                            ),
                            ("is_moodle", "=", True),
                            ("survey_type", "=", result_type),
                        ],
                        limit=1,
                    )
                    grade = round(data["avg"], 2)
                    valid_lines.append(
                        dict(
                            base_values,
                            state="ok",
                            apply_line=True,
                            survey_type=result_type,
                            moodle_grade=grade,
                            grade_to_apply=grade,
                            current_grade=(
                                current.scoring_total if current else 0.0
                            ),
                            graded_count=data["graded"],
                            moodle_info=" | ".join(data["found"]),
                        )
                    )
                if compatibility_conflict:
                    line_model.create(
                        dict(
                            base_values,
                            state="incompatible",
                            apply_line=False,
                            moodle_info=compatibility_conflict,
                        )
                    )
                    break
                if valid_lines:
                    line_model.create(valid_lines)
                    methods.add(method)
                    break
                attempts.append(
                    _("%s: %s")
                    % (prefix, " ".join(dict.fromkeys(reasons)))
                )
            else:
                line_model.create(
                    dict(
                        base_values,
                        state="incompatible",
                        apply_line=False,
                        moodle_info=_(
                            "No se obtuvo una nota válida de los cursos "
                            "HomeClass: %s"
                        )
                        % " | ".join(attempts),
                    )
                )

        self.match_method = ", ".join(sorted(methods)) or False
        return True

    def action_load_moodle_data(self):
        self.ensure_one()
        candidates = self._irg_homeclass_candidates()
        if len(candidates) > 1:
            return self._irg_load_multiple_homeclass(candidates)
        return super().action_load_moodle_data()
