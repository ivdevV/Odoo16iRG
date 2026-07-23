import base64
import binascii

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from ..services.mapping_import import MAX_FILE_SIZE, MappingImportService


MAX_BASE64_SIZE = 4 * ((MAX_FILE_SIZE + 2) // 3)
UPLOAD_FIELDS = ("courses_file", "assignments_file")
SERVER_OWNED_FIELDS = {
    "state",
    "summary_text",
    "affected_course_map_ids",
    "affected_subject_map_ids",
}
REASON_LABELS = {
    "activity_name_count_mismatch": (
        "cantidad de nombres de actividad distinta de los identificadores"
    ),
    "ambiguous_course_alias": "alias de curso contradictorios",
    "blank_row": "fila vacía",
    "code_mismatch": "código de asignatura no coincidente",
    "conflicting_subject_parent": "curso Odoo padre contradictorio",
    "duplicate_activity_id": "identificador de actividad duplicado",
    "invalid_id": "identificador inválido",
    "invalid_online_marker": "marcador Online inválido",
    "missing_course_pair": "pareja curso Odoo/Moodle ausente",
    "missing_odoo_record": "registro Odoo inexistente",
    "name_mismatch": "nombre no coincidente",
    "no_activity_ids": "sin identificadores de actividad",
    "subject_not_in_course": "asignatura ajena al curso Odoo",
}
SERVICE_ERROR_MESSAGES = {
    "CSV courses: invalid binary payload": (
        "El contenido del CSV de cursos no es un binario válido."
    ),
    "CSV assignments: invalid binary payload": (
        "El contenido del CSV de asignaturas no es un binario válido."
    ),
    "CSV courses exceeds 10 MiB": "El CSV de cursos supera 10 MiB.",
    "CSV assignments exceeds 10 MiB": "El CSV de asignaturas supera 10 MiB.",
    "CSV courses cannot be parsed": "No se pudo interpretar el CSV de cursos.",
    "CSV assignments cannot be parsed": (
        "No se pudo interpretar el CSV de asignaturas."
    ),
    "CSV courses: missing required header(s)": (
        "El CSV de cursos no contiene todas las cabeceras obligatorias."
    ),
    "CSV assignments: missing required header(s)": (
        "El CSV de asignaturas no contiene todas las cabeceras obligatorias."
    ),
}
GENERIC_REASON_LABEL = "otro motivo de validación"
GENERIC_SERVICE_ERROR = (
    "No se pudieron analizar los archivos CSV. Revise el formato y las cabeceras."
)


class IrgGradebookMoodleMappingImportWizard(models.TransientModel):
    _name = "irg.gradebook.moodle.mapping.import.wizard"
    _description = "Importar mapeo Moodle"

    courses_file = fields.Binary(string="mapeo cursos.csv", required=True)
    courses_filename = fields.Char()
    assignments_file = fields.Binary(
        string="Mapeo asignaturas.csv", required=True
    )
    assignments_filename = fields.Char()
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("validated", "Validado"),
            ("applied", "Aplicado"),
        ],
        default="draft",
        required=True,
        readonly=True,
    )
    summary_text = fields.Text(readonly=True)
    affected_course_map_ids = fields.Many2many(
        "irg.gradebook.moodle.course.map",
        "irg_mapping_import_course_rel",
        "wizard_id",
        "course_map_id",
        readonly=True,
    )
    affected_subject_map_ids = fields.Many2many(
        "irg.gradebook.moodle.map",
        "irg_mapping_import_subject_rel",
        "wizard_id",
        "subject_map_id",
        readonly=True,
    )

    def _check_admin(self):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(
                _("Solo los administradores pueden importar el mapeo Moodle.")
            )

    def _check_encoded_upload(self, value, label):
        if value is False or value is None:
            return
        if not isinstance(value, (bytes, str)):
            raise ValidationError(
                _("El archivo %s no es un binario válido.") % label
            )
        if len(value) > MAX_BASE64_SIZE:
            raise ValidationError(_("El archivo %s supera 10 MiB.") % label)

    def _decode_upload(self, value, label):
        if not value:
            raise ValidationError(_("Debe adjuntar %s.") % label)
        self._check_encoded_upload(value, label)
        try:
            payload = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValidationError(
                _("El archivo %s no es válido.") % label
            ) from error
        if len(payload) > MAX_FILE_SIZE:
            raise ValidationError(_("El archivo %s supera 10 MiB.") % label)
        return payload

    @api.model_create_multi
    def create(self, vals_list):
        self._check_admin()
        clean_values = []
        for values in vals_list:
            values = dict(values)
            for field_name, label in self._upload_labels().items():
                if field_name in values:
                    self._check_encoded_upload(values[field_name], label)
            for field_name in SERVER_OWNED_FIELDS:
                values.pop(field_name, None)
            clean_values.append(values)
        return super().create(clean_values)

    def write(self, values):
        self._check_admin()
        values = dict(values)
        changed_upload = any(field_name in values for field_name in UPLOAD_FIELDS)
        for field_name, label in self._upload_labels().items():
            if field_name in values:
                self._check_encoded_upload(values[field_name], label)
        if changed_upload:
            values.update(
                {
                    "state": "draft",
                    "summary_text": False,
                    "affected_course_map_ids": [Command.clear()],
                    "affected_subject_map_ids": [Command.clear()],
                }
            )
        elif SERVER_OWNED_FIELDS.intersection(values):
            raise ValidationError(
                _("El estado y el resultado de la importación son internos.")
            )
        return super().write(values)

    def action_validate(self):
        self._check_admin()
        self.ensure_one()
        self._require_state("draft")
        plan = self._analyze_persisted_uploads()
        self._write_internal(
            {"state": "validated", "summary_text": self._format_summary(plan.summary)}
        )
        return self._reopen_action()

    def action_apply(self):
        self._check_admin()
        self.ensure_one()
        self._require_state("validated")
        plan = self._analyze_persisted_uploads()
        result = MappingImportService(self.env).apply_plan(plan)
        self._write_internal(
            {
                "state": "applied",
                "summary_text": self._format_summary(plan.summary, result),
                "affected_course_map_ids": [
                    Command.set(result["affected_course_map_ids"])
                ],
                "affected_subject_map_ids": [
                    Command.set(result["affected_subject_map_ids"])
                ],
            }
        )
        return self._reopen_action()

    def action_open_course_maps(self):
        self._check_admin()
        self.ensure_one()
        self._require_state("applied")
        action = self.env.ref(
            "irg_gradebook_moodle_routing.action_irg_gradebook_moodle_course_map"
        ).read()[0]
        action["domain"] = [("id", "in", self.affected_course_map_ids.ids)]
        return action

    def action_open_subject_maps(self):
        self._check_admin()
        self.ensure_one()
        self._require_state("applied")
        action = self.env.ref(
            "irg_gradebook_moodle_wizard.act_irg_gradebook_moodle_map"
        ).read()[0]
        action["domain"] = [("id", "in", self.affected_subject_map_ids.ids)]
        return action

    @staticmethod
    def _upload_labels():
        return {
            "courses_file": "mapeo cursos.csv",
            "assignments_file": "Mapeo asignaturas.csv",
        }

    def _require_state(self, expected_state):
        if self.state != expected_state:
            raise ValidationError(
                _("La importación no está en el estado requerido.")
            )

    def _analyze_persisted_uploads(self):
        courses_payload = self._decode_upload(
            self.courses_file, "mapeo cursos.csv"
        )
        assignments_payload = self._decode_upload(
            self.assignments_file, "Mapeo asignaturas.csv"
        )
        try:
            return MappingImportService(self.env).analyze_bytes(
                courses_payload, assignments_payload
            )
        except ValueError as error:
            message = SERVICE_ERROR_MESSAGES.get(
                str(error), GENERIC_SERVICE_ERROR
            )
            raise ValidationError(message) from None

    def _write_internal(self, values):
        return super(IrgGradebookMoodleMappingImportWizard, self).write(values)

    def _reopen_action(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Importar mapeo Moodle"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @staticmethod
    def _format_summary(summary, result=None):
        labels = (("courses", "Cursos"), ("assignments", "Asignaturas"))
        lines = []
        for key, label in labels:
            stats = summary[key]
            lines.append(
                "%s: leídas %s; válidas %s; omitidas %s; advertidas %s."
                % (
                    label,
                    stats["rows_read"],
                    stats["rows_accepted"],
                    stats["rows_skipped"],
                    stats["rows_warned"],
                )
            )
            for bucket, reason_label in (
                ("skipped_by_reason", "Omitidas"),
                ("warned_by_reason", "Advertencias"),
            ):
                reasons = stats[bucket]
                if reasons:
                    detail = ", ".join(
                        "%s=%s"
                        % (REASON_LABELS.get(reason, GENERIC_REASON_LABEL), count)
                        for reason, count in sorted(reasons.items())
                    )
                    lines.append("%s %s: %s." % (reason_label, label.lower(), detail))
        changes = result or summary
        if all(
            key in changes
            for key in ("course_maps", "subject_maps", "activities")
        ):
            if result:
                course_template = "Mapas de curso: creados %s; actualizados %s."
                subject_template = (
                    "Mapas de asignatura: creados %s; actualizados %s."
                )
                activity_template = "Actividades: creadas %s; actualizadas %s."
            else:
                course_template = (
                    "Mapas de curso: se crearán %s; se actualizarán %s."
                )
                subject_template = (
                    "Mapas de asignatura: se crearán %s; se actualizarán %s."
                )
                activity_template = (
                    "Actividades: se crearán %s; se actualizarán %s."
                )
            lines.extend(
                [
                    course_template
                    % (
                        changes["course_maps"]["created"],
                        changes["course_maps"]["updated"],
                    ),
                    subject_template
                    % (
                        changes["subject_maps"]["created"],
                        changes["subject_maps"]["updated"],
                    ),
                    activity_template
                    % (
                        changes["activities"]["created"],
                        changes["activities"]["updated"],
                    ),
                ]
            )
        return "\n".join(lines)
