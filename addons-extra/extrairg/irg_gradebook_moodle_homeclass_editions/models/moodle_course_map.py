import re

from odoo import api, fields, models


HOMECLASS_PERIOD_RE = re.compile(
    r"(?<!\d)(20\d{2})\s*[-/_]\s*(20\d{2})(?!\d)"
)


def extract_homeclass_start_year(name):
    """Return the start of the first valid academic period in ``name``."""
    for match in HOMECLASS_PERIOD_RE.finditer(name or ""):
        start_year, end_year = map(int, match.groups())
        if end_year == start_year + 1:
            return start_year
    return False


class IrgGradebookMoodleCourseMap(models.Model):
    _inherit = "irg.gradebook.moodle.course.map"

    irg_homeclass_edition_override = fields.Integer(
        string="Edición HomeClass manual"
    )

    @api.depends("moodle_course_name", "irg_homeclass_edition_override")
    def _compute_routing_metadata(self):
        super()._compute_routing_metadata()
        for record in self.filtered(lambda item: item.modality == "homeclass"):
            record.edition_year = (
                record.irg_homeclass_edition_override
                or extract_homeclass_start_year(record.moodle_course_name)
            )
