import math

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.irg_moodle_grades_sync.models import utils as sync_utils
from odoo.addons.irg_moodle_grades_sync.models.utils import parse_grade
from odoo.addons.odoo_moodle_connector.models import utils as connector_utils

from ..models.gradebook_service import GradebookMoodleService


TYPE_BY_ACTIVITY = {"quiz": "exam", "assign": "assignment"}


class IrgGradebookMoodleSyncWizard(models.TransientModel):
    _name = "irg.gradebook.moodle.sync.wizard"
    _description = "Wizard sincronización notas Moodle -> libreta"

    gradebook_student_id = fields.Many2one(
        "app.gradebook.student", string="Libreta", required=True
    )
    student_id = fields.Many2one(
        related="gradebook_student_id.student_id", string="Alumno"
    )
    match_method = fields.Char(string="Emparejado por", readonly=True)
    line_ids = fields.One2many(
        "irg.gradebook.moodle.sync.wizard.line",
        "wizard_id",
        string="Notas encontradas",
    )

    def _get_service(self):
        credentials = connector_utils.get_moodle_credentials(self.env)
        if not credentials:
            raise UserError(
                _(
                    "No hay credenciales de Moodle configuradas. "
                    "Configúralas en el módulo Odoo Moodle Connector."
                )
            )
        return GradebookMoodleService(credentials, self.env)

    def _check_moodle_sync_access(self):
        self.ensure_one()
        return self.gradebook_student_id._check_moodle_sync_access()

    @staticmethod
    def _find_student_entry(partner, student_name, usergrades, emails):
        """Match a Moodle user by md_id, email, then unique normalized name."""
        md_id = getattr(partner, "md_id", False)
        if md_id:
            for entry in usergrades:
                if entry.get("userid") == md_id:
                    return entry, "md_id"

        email = (partner.email or "").strip().lower()
        if email:
            for entry in usergrades:
                if (
                    emails.get(entry.get("userid"), "").strip().lower()
                    == email
                ):
                    return entry, "email"

        target = sync_utils.normalize_name(student_name)
        if target:
            matches = [
                entry
                for entry in usergrades
                if sync_utils.normalize_name(entry.get("userfullname"))
                == target
            ]
            if len(matches) == 1:
                return matches[0], "name"
        return None, None

    @staticmethod
    def _grades_by_type(entry, map_lines, grading_scale):
        """Resolve each map line exactly once, then aggregate valid grades."""
        items = entry.get("gradeitems", [])
        result_types = {
            TYPE_BY_ACTIVITY.get(line.activity_type, "exam")
            for line in map_lines
        }
        resolved = []
        issues = {result_type: [] for result_type in result_types}
        item_usage = {}

        for map_line in map_lines:
            result_type = TYPE_BY_ACTIVITY.get(map_line.activity_type, "exam")
            activity_id = map_line.moodle_activity_id
            matches = [
                (index, item)
                for index, item in enumerate(items)
                if item.get("id") == activity_id
                or item.get("cmid") == activity_id
            ]
            if len(matches) != 1:
                issues[result_type].append(
                    _(
                        "La actividad Moodle %s tiene una resolución ambigua "
                        "(%s coincidencias por id/cmid)."
                    )
                    % (activity_id, len(matches))
                )
                continue
            item_index, item = matches[0]
            resolved.append((map_line, result_type, item_index, item))
            item_usage.setdefault(item_index, []).append(
                (map_line, result_type)
            )

        for usages in item_usage.values():
            if len(usages) > 1:
                for map_line, result_type in usages:
                    issues[result_type].append(
                        _(
                            "La actividad Moodle %s tiene una resolución "
                            "ambigua: el mismo grade item se reutiliza."
                        )
                        % map_line.moodle_activity_id
                    )

        result = {}
        for result_type in result_types:
            type_rows = [row for row in resolved if row[1] == result_type]
            found = [
                item.get("itemname") or str(map_line.moodle_activity_id)
                for map_line, _result_type, _item_index, item in type_rows
            ]
            if issues[result_type]:
                result[result_type] = {
                    "avg": None,
                    "found": found,
                    "graded": 0,
                    "error": " ".join(dict.fromkeys(issues[result_type])),
                }
                continue

            grades = []
            for _map_line, _result_type, _item_index, item in type_rows:
                grade = parse_grade(item.get("graderaw"))
                grade_max = parse_grade(item.get("grademax"))
                if (
                    grade is None
                    or not math.isfinite(grade)
                    or grade_max is None
                    or not math.isfinite(grade_max)
                    or grade_max <= 0
                ):
                    continue
                grades.append(grade / grade_max * grading_scale)
            result[result_type] = {
                "avg": sum(grades) / len(grades) if grades else None,
                "found": found,
                "graded": len(grades),
                "error": False,
            }
        return result

    @staticmethod
    def _compatibility_reason(gradebook_subject, result_type):
        gradebook = (
            gradebook_subject.gradebook_id
            or gradebook_subject.gradebook_student_id.gradebook_id
        )
        template_lines = gradebook.gradebook_template_ids.filtered(
            lambda line: line.type == result_type
        )
        if len(template_lines) != 1 or template_lines.qty != 1:
            return _(
                "El template efectivo debe tener cantidad exactamente 1 "
                "para este tipo."
            )

        results = gradebook_subject.gradebook_result_ids.filtered(
            lambda result: result.survey_type == result_type
        )
        if results.filtered(lambda result: not result.is_moodle):
            return _(
                "Existe una nota manual del mismo tipo; Moodle no puede "
                "reemplazarla ni mezclarla."
            )
        if len(results.filtered("is_moodle")) > 1:
            return _(
                "Existen notas Moodle duplicadas para la asignatura y tipo."
            )
        return False

    def action_load_moodle_data(self):
        self.ensure_one()
        self._check_moodle_sync_access()
        self.line_ids.unlink()
        service = self._get_service()
        gradebook_student = self.gradebook_student_id
        scale = gradebook_student.gradebook_id.grading_scale or 10.0
        map_model = self.env["irg.gradebook.moodle.map"]
        line_model = self.env["irg.gradebook.moodle.sync.wizard.line"]
        result_model = self.env["app.gradebook.result"]
        course_cache = {}
        methods = set()

        for gradebook_subject in gradebook_student.gradebook_subject_ids:
            subject = gradebook_subject.op_subject_id
            subject_maps = map_model.search(
                [("op_subject_id", "=", subject.id), ("active", "=", True)]
            )
            base_values = {
                "wizard_id": self.id,
                "gradebook_subject_id": gradebook_subject.id,
                "subject_id": subject.id,
            }
            if not subject_maps:
                line_model.create(
                    dict(base_values, state="sin_mapeo", apply_line=False)
                )
                continue

            if len(subject_maps) > 1:
                line_model.create(
                    dict(
                        base_values,
                        state="incompatible",
                        apply_line=False,
                        moodle_info=_(
                            "Hay más de un mapa Moodle activo para esta "
                            "asignatura."
                        ),
                    )
                )
                continue

            subject_map = subject_maps
            if not subject_map.line_ids:
                line_model.create(
                    dict(base_values, state="sin_mapeo", apply_line=False)
                )
                continue

            if subject_map.moodle_course_id not in course_cache:
                course_cache[subject_map.moodle_course_id] = (
                    service.get_user_grade_items(subject_map.moodle_course_id)
                )
            usergrades, emails = course_cache[subject_map.moodle_course_id]
            entry, method = self._find_student_entry(
                gradebook_student.partner_id,
                gradebook_student.student_id.name,
                usergrades,
                emails,
            )
            if entry is None:
                line_model.create(
                    dict(
                        base_values,
                        state="alumno_no_encontrado",
                        apply_line=False,
                        moodle_info=subject_map.moodle_course_name or "",
                    )
                )
                continue

            methods.add(method)
            grades_by_type = self._grades_by_type(
                entry, subject_map.line_ids, scale
            )
            for result_type, data in grades_by_type.items():
                compatibility_reason = self._compatibility_reason(
                    gradebook_subject, result_type
                )
                if data["error"] or compatibility_reason:
                    details = [
                        detail
                        for detail in (data["error"], compatibility_reason)
                        if detail
                    ]
                    line_model.create(
                        dict(
                            base_values,
                            state="incompatible",
                            apply_line=False,
                            survey_type=result_type,
                            moodle_info=" ".join(details),
                        )
                    )
                    continue
                current = result_model.search(
                    [
                        ("gradebook_subject_id", "=", gradebook_subject.id),
                        ("is_moodle", "=", True),
                        ("survey_type", "=", result_type),
                    ],
                    limit=1,
                )
                if data["avg"] is None:
                    line_model.create(
                        dict(
                            base_values,
                            state="sin_nota",
                            apply_line=False,
                            survey_type=result_type,
                            moodle_info=" | ".join(data["found"]),
                        )
                    )
                    continue
                grade = round(data["avg"], 2)
                line_model.create(
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

        self.match_method = ", ".join(sorted(methods)) or False
        return True

    def _validate_apply_lines(self):
        self.ensure_one()
        self._check_moodle_sync_access()
        gradebook_student = self.gradebook_student_id
        gradebook_student.check_access_rights("write")
        gradebook_student.check_access_rule("write")
        if gradebook_student.state == "done":
            raise UserError(_("No se puede modificar una libreta finalizada."))

        all_moodle_results = self.env["app.gradebook.result"].search(
            [
                (
                    "gradebook_subject_id",
                    "in",
                    gradebook_student.gradebook_subject_ids.ids,
                ),
                ("is_moodle", "=", True),
            ]
        )
        all_moodle_results.check_access_rights("read")
        all_moodle_results.check_access_rule("read")
        seen_global_keys = set()
        for result in all_moodle_results:
            key = (result.gradebook_subject_id.id, result.survey_type)
            if key in seen_global_keys:
                raise UserError(
                    _(
                        "Existen notas Moodle duplicadas; corrija la "
                        "integridad antes de aplicar."
                    )
                )
            seen_global_keys.add(key)

        lines = self.line_ids.filtered("apply_line").sorted(
            key=lambda line: (line.gradebook_subject_id.id, line.survey_type or "")
        )
        if not lines:
            return lines, []

        result_model = self.env["app.gradebook.result"]
        result_model.check_access_rights("create")
        allowed_subjects = gradebook_student.gradebook_subject_ids
        allowed_subjects.check_access_rights("write")
        allowed_subjects.check_access_rule("write")
        grading_scale = gradebook_student.gradebook_id.grading_scale
        keys = set()
        subject_ids = []

        for line in lines:
            if line.state != "ok":
                raise UserError(
                    _(
                        "Solo se pueden aplicar líneas con estado "
                        "Encontrada."
                    )
                )
            gradebook_subject = line.gradebook_subject_id
            if (
                not gradebook_subject
                or gradebook_subject not in allowed_subjects
                or line.subject_id != gradebook_subject.op_subject_id
                or line.wizard_id != self
            ):
                raise UserError(
                    _("Una línea no pertenece a la libreta seleccionada.")
                )
            if line.survey_type not in TYPE_BY_ACTIVITY.values():
                raise UserError(_("Una línea aplicable no tiene un tipo válido."))

            key = (gradebook_subject.id, line.survey_type)
            if key in keys:
                raise UserError(
                    _("Hay líneas aplicables repetidas para asignatura y tipo.")
                )
            keys.add(key)
            subject_ids.append(gradebook_subject.id)

            grade = line.grade_to_apply
            if (
                not math.isfinite(grade)
                or grade < 0
                or grade > grading_scale
            ):
                raise UserError(
                    _(
                        "La nota a aplicar debe ser finita y estar entre 0 "
                        "y %s."
                    )
                    % grading_scale
                )

            incompatibility = self._compatibility_reason(
                gradebook_subject, line.survey_type
            )
            if incompatibility:
                raise UserError(incompatibility)

            existing = result_model.search(
                [
                    ("gradebook_subject_id", "=", gradebook_subject.id),
                    ("is_moodle", "=", True),
                    ("survey_type", "=", line.survey_type),
                ]
            )
            if len(existing) > 1:
                raise UserError(
                    _(
                        "Existen notas Moodle duplicadas; corrija la "
                        "integridad antes de aplicar."
                    )
                )
            existing.check_access_rights("write")
            existing.check_access_rule("write")

        return lines, sorted(set(subject_ids))

    def _lock_apply_lines(self):
        self.env.cr.execute(
            """
            SELECT id
              FROM irg_gradebook_moodle_sync_wizard_line
             WHERE wizard_id = %s
             ORDER BY id
             FOR UPDATE
            """,
            (self.id,),
        )
        return [row[0] for row in self.env.cr.fetchall()]

    def _invalidate_apply_lines(self, line_ids):
        self.invalidate_recordset(["line_ids"])
        lines = self.env[
            "irg.gradebook.moodle.sync.wizard.line"
        ].browse(line_ids)
        lines.invalidate_recordset()
        if sorted(self.line_ids.ids) != line_ids:
            raise UserError(
                _("Las líneas del asistente cambiaron durante el proceso.")
            )

    def _lock_apply_subjects(self, subject_ids):
        self.env.cr.execute(
            """
            SELECT id
              FROM app_gradebook_subject
             WHERE id = ANY(%s)
             ORDER BY id
             FOR UPDATE
            """,
            (subject_ids,),
        )
        locked_ids = [row[0] for row in self.env.cr.fetchall()]
        if locked_ids != subject_ids:
            raise UserError(
                _("Una asignatura dejó de estar disponible durante el proceso.")
            )
        self.env.cr.execute(
            """
            UPDATE app_gradebook_subject
               SET write_date = write_date
             WHERE id = ANY(%s)
            """,
            (subject_ids,),
        )

    def action_apply(self):
        self.ensure_one()
        self._check_moodle_sync_access()
        locked_line_ids = self._lock_apply_lines()
        self._invalidate_apply_lines(locked_line_ids)
        lines, subject_ids = self._validate_apply_lines()
        if subject_ids:
            self._lock_apply_subjects(subject_ids)
        self.invalidate_recordset()
        self.gradebook_student_id.invalidate_recordset()
        self.env["app.gradebook.subject"].browse(
            subject_ids
        ).invalidate_recordset()
        self.env["app.gradebook.result"].invalidate_model()
        self._invalidate_apply_lines(locked_line_ids)
        lines_after_lock, subject_ids_after_lock = self._validate_apply_lines()
        if (
            lines_after_lock.ids != lines.ids
            or subject_ids_after_lock != subject_ids
        ):
            raise UserError(
                _("Las líneas aplicables cambiaron durante el proceso.")
            )
        lines = lines_after_lock
        result_model = self.env["app.gradebook.result"]
        applied = 0
        for line in lines:
            values = {
                "scoring_total": line.grade_to_apply,
                "description": _("Moodle · media de %s actividades")
                % line.graded_count,
                "is_moodle": True,
                "survey_type": line.survey_type,
                "gradebook_subject_id": line.gradebook_subject_id.id,
            }
            existing = result_model.search(
                [
                    (
                        "gradebook_subject_id",
                        "=",
                        line.gradebook_subject_id.id,
                    ),
                    ("is_moodle", "=", True),
                    ("survey_type", "=", line.survey_type),
                ],
            )
            if existing:
                existing.write(values)
            else:
                result_model.create(values)
            applied += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Notas Moodle aplicadas"),
                "message": _("%s líneas escritas en la libreta.") % applied,
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }


class IrgGradebookMoodleSyncWizardLine(models.TransientModel):
    _name = "irg.gradebook.moodle.sync.wizard.line"
    _description = "Línea del wizard de sincronización Moodle"
    _order = "subject_id, survey_type"

    wizard_id = fields.Many2one(
        "irg.gradebook.moodle.sync.wizard", required=True, ondelete="cascade"
    )
    gradebook_subject_id = fields.Many2one(
        "app.gradebook.subject", string="Asignatura libreta"
    )
    subject_id = fields.Many2one("op.subject", string="Asignatura")
    survey_type = fields.Selection(
        [("exam", "Examen"), ("assignment", "Asignación")], string="Tipo"
    )
    moodle_info = fields.Text(string="Actividades Moodle")
    graded_count = fields.Integer(string="Con nota")
    moodle_grade = fields.Float(string="Nota Moodle (escala libreta)")
    grade_to_apply = fields.Float(string="Nota a aplicar")
    current_grade = fields.Float(string="Nota actual", readonly=True)
    state = fields.Selection(
        [
            ("ok", "Encontrada"),
            ("sin_mapeo", "Sin mapeo"),
            ("sin_nota", "Sin nota en Moodle"),
            ("alumno_no_encontrado", "Alumno no encontrado"),
            ("incompatible", "Incompatible"),
        ],
        string="Estado",
        default="ok",
    )
    apply_line = fields.Boolean(string="Aplicar", default=True)
