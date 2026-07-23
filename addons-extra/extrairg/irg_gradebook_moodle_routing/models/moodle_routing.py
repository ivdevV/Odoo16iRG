import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


COURSE_MAP_CONTEXT_KEY = "irg_gradebook_moodle_course_map_id"
ONLINE_MARKER_RE = re.compile(
    r"\(ONLINE(?: ([0-9]{4}))?\)", re.IGNORECASE
)


def parse_moodle_course_name(name):
    """Return routing metadata, rejecting every malformed Online marker."""
    normalized_name = (name or "").strip()
    if not normalized_name:
        return False, False
    if "(ONLINE" not in normalized_name.upper():
        return "homeclass", False

    matches = list(ONLINE_MARKER_RE.finditer(normalized_name))
    if len(matches) != 1:
        return False, False
    marker = matches[0]
    remaining_name = (
        normalized_name[: marker.start()] + normalized_name[marker.end() :]
    )
    if "(ONLINE" in remaining_name.upper():
        return False, False

    edition_year = int(marker.group(1)) if marker.group(1) else False
    return "online", edition_year


class IrgGradebookMoodleCourseMap(models.Model):
    _name = "irg.gradebook.moodle.course.map"
    _description = "Mapeo curso Odoo a curso Moodle"
    _order = "op_course_id, modality, edition_year, moodle_course_id"
    _rec_name = "moodle_course_name"

    op_course_id = fields.Many2one(
        "op.course", required=True, index=True, ondelete="restrict"
    )
    moodle_course_id = fields.Integer(required=True, index=True)
    moodle_course_name = fields.Char(required=True)
    modality = fields.Selection(
        [("homeclass", "HomeClass"), ("online", "Online")],
        compute="_compute_routing_metadata",
        store=True,
        readonly=True,
    )
    edition_year = fields.Integer(
        compute="_compute_routing_metadata", store=True, readonly=True
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "course_moodle_uniq",
            "unique(op_course_id, moodle_course_id)",
            "Ya existe un mapeo para este curso Odoo y curso Moodle.",
        ),
        (
            "moodle_course_id_positive",
            "CHECK(moodle_course_id > 0)",
            "El ID del curso Moodle debe ser positivo.",
        ),
    ]

    @api.depends("moodle_course_name")
    def _compute_routing_metadata(self):
        for record in self:
            record.modality, record.edition_year = parse_moodle_course_name(
                record.moodle_course_name
            )

    @api.constrains("op_course_id", "moodle_course_id")
    def _check_subject_map_integrity(self):
        subject_maps = self.env["irg.gradebook.moodle.map"].with_context(
            active_test=False
        ).search([("course_map_id", "in", self.ids)])
        error = subject_maps._irg_parent_integrity_error()
        if error:
            raise ValidationError(error)


class IrgGradebookMoodleMap(models.Model):
    _inherit = "irg.gradebook.moodle.map"

    course_map_id = fields.Many2one(
        "irg.gradebook.moodle.course.map",
        index=True,
        ondelete="restrict",
    )

    def _irg_parent_integrity_error(self):
        for mapping in self:
            parent = mapping.course_map_id
            if not parent:
                continue
            if mapping.moodle_course_id != parent.moodle_course_id:
                return _(
                    "El mapa de asignatura y su mapa de curso padre deben "
                    "usar el mismo ID de curso Moodle."
                )
            if mapping.op_subject_id not in parent.op_course_id.subject_ids:
                return _(
                    "La asignatura del mapa no pertenece al curso Odoo "
                    "del mapa padre."
                )
        return False

    @api.constrains("course_map_id", "moodle_course_id", "op_subject_id")
    def _check_course_map_integrity(self):
        error = self._irg_parent_integrity_error()
        if error:
            raise ValidationError(error)

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        if COURSE_MAP_CONTEXT_KEY in self.env.context:
            args = list(args or []) + [
                (
                    "course_map_id",
                    "=",
                    self.env.context[COURSE_MAP_CONTEXT_KEY],
                )
            ]
        return super()._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
            access_rights_uid=access_rights_uid,
        )
