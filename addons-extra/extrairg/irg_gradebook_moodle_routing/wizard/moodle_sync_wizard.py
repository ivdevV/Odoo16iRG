from odoo import _, models
from odoo.exceptions import UserError

from ..models.moodle_routing import COURSE_MAP_CONTEXT_KEY


class IrgGradebookMoodleSyncWizard(models.TransientModel):
    _inherit = "irg.gradebook.moodle.sync.wizard"

    def _irg_resolve_course_map(self):
        self.ensure_one()
        gradebook_student = self.gradebook_student_id
        batch = gradebook_student.batch_id
        batch_code = (batch.code or "").upper()
        is_homeclass = "HC" in batch_code
        is_online = "ONL" in batch_code
        if is_homeclass == is_online:
            raise UserError(
                _(
                    "El código del lote debe identificar una única modalidad "
                    "Moodle mediante HC u ONL."
                )
            )

        modality = "homeclass" if is_homeclass else "online"
        candidates = self.env["irg.gradebook.moodle.course.map"].search(
            [
                ("op_course_id", "=", gradebook_student.course_id.id),
                ("modality", "=", modality),
                ("active", "=", True),
            ]
        )
        if modality == "homeclass":
            if len(candidates) != 1:
                raise UserError(
                    _(
                        "El curso debe tener exactamente un mapa Moodle "
                        "HomeClass activo; se encontraron %s."
                    )
                    % len(candidates)
                )
            return candidates

        edition_year = batch.start_date.year if batch.start_date else False
        if edition_year:
            edition_candidates = candidates.filtered(
                lambda mapping: mapping.edition_year == edition_year
            )
            if len(edition_candidates) > 1:
                raise UserError(
                    _(
                        "Hay más de un mapa Moodle online activo para la "
                        "edición %s."
                    )
                    % edition_year
                )
            if len(edition_candidates) == 1:
                return edition_candidates

        generic_candidates = candidates.filtered(
            lambda mapping: not mapping.edition_year
        )
        if len(generic_candidates) != 1:
            raise UserError(
                _(
                    "No existe un único mapa Moodle online genérico para "
                    "usar como alternativa; se encontraron %s."
                )
                % len(generic_candidates)
            )
        return generic_candidates

    def action_load_moodle_data(self):
        self.ensure_one()
        self._check_moodle_sync_access()
        course_map = self._irg_resolve_course_map()
        routed_wizard = self.with_context(
            **{COURSE_MAP_CONTEXT_KEY: course_map.id}
        )
        subject_maps = routed_wizard.env["irg.gradebook.moodle.map"].search(
            [("active", "=", True)]
        )
        integrity_error = subject_maps._irg_parent_integrity_error()
        if integrity_error:
            raise UserError(
                _("El routing Moodle contiene un mapa incoherente: %s")
                % integrity_error
            )
        return super(
            IrgGradebookMoodleSyncWizard, routed_wizard
        ).action_load_moodle_data()
