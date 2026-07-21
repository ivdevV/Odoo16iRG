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
        """Scale and aggregate mapped grade items by gradebook result type."""
        wanted = {
            line.moodle_activity_id: TYPE_BY_ACTIVITY.get(
                line.activity_type, "exam"
            )
            for line in map_lines
        }
        buckets = {"exam": [], "assignment": []}
        found = {"exam": [], "assignment": []}

        for item in entry.get("gradeitems", []):
            key = None
            if item.get("id") in wanted:
                key = item["id"]
            elif item.get("cmid") in wanted:
                key = item["cmid"]
            if key is None:
                continue

            result_type = wanted[key]
            found[result_type].append(item.get("itemname") or str(key))
            grade = parse_grade(item.get("graderaw"))
            if grade is None:
                continue
            grade_max = item.get("grademax") or 0.0
            if grade_max and grading_scale:
                grade = grade / grade_max * grading_scale
            buckets[result_type].append(grade)

        result = {}
        for result_type in ("exam", "assignment"):
            grades = buckets[result_type]
            result[result_type] = {
                "avg": sum(grades) / len(grades) if grades else None,
                "found": found[result_type],
                "graded": len(grades),
            }
        return result

    def action_load_moodle_data(self):
        self.ensure_one()
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
            subject_map = map_model.search(
                [("op_subject_id", "=", subject.id), ("active", "=", True)],
                limit=1,
            )
            base_values = {
                "wizard_id": self.id,
                "gradebook_subject_id": gradebook_subject.id,
                "subject_id": subject.id,
            }
            if not subject_map or not subject_map.line_ids:
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
                if not data["found"]:
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

    def action_apply(self):
        self.ensure_one()
        result_model = self.env["app.gradebook.result"]
        applied = 0
        lines = self.line_ids.filtered(
            lambda line: line.apply_line and line.state == "ok"
        )
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
                limit=1,
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
        ],
        string="Estado",
        default="ok",
    )
    apply_line = fields.Boolean(string="Aplicar", default=True)
