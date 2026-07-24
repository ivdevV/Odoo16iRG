import math

from odoo import _, models

from odoo.addons.irg_gradebook_moodle_wizard.models.gradebook_service import (
    GradebookMoodleService,
)
from odoo.addons.irg_gradebook_moodle_wizard.wizard.moodle_sync_wizard import (
    TYPE_BY_ACTIVITY,
)
from odoo.addons.irg_moodle_grades_sync.models.utils import parse_grade
from odoo.addons.odoo_moodle_connector.models import utils as connector_utils

from ..models.gradebook_service import IteminstanceGradebookMoodleService


class IrgGradebookMoodleSyncWizard(models.TransientModel):
    _inherit = "irg.gradebook.moodle.sync.wizard"

    def _get_service(self):
        base_service = super()._get_service()
        if not isinstance(base_service, GradebookMoodleService):
            return base_service
        credentials = connector_utils.get_moodle_credentials(self.env)
        return IteminstanceGradebookMoodleService(credentials, self.env)

    @staticmethod
    def _irg_match_grade_items(items, activity_id):
        """Return each grade item once when any supported ID matches."""
        return [
            (index, item)
            for index, item in enumerate(items)
            if activity_id
            in (
                item.get("id"),
                item.get("cmid"),
                item.get("iteminstance"),
            )
        ]

    def _grades_by_type(self, entry, map_lines, grading_scale):
        """Resolve mapped activities across every Moodle ID namespace."""
        items = entry.get("gradeitems", [])
        result_types = {
            TYPE_BY_ACTIVITY.get(line.activity_type, "exam")
            for line in map_lines
        }
        resolved = []
        issues = {result_type: [] for result_type in result_types}
        item_usage = {}

        for map_line in map_lines:
            result_type = TYPE_BY_ACTIVITY.get(
                map_line.activity_type, "exam"
            )
            activity_id = map_line.moodle_activity_id
            matches = self._irg_match_grade_items(items, activity_id)
            if not matches:
                issues[result_type].append(
                    _(
                        "No se encontró la actividad Moodle %s por "
                        "id/cmid/iteminstance."
                    )
                    % activity_id
                )
                continue
            if len(matches) > 1:
                issues[result_type].append(
                    _(
                        "La actividad Moodle %s tiene una resolución ambigua "
                        "(%s coincidencias por id/cmid/iteminstance)."
                    )
                    % (activity_id, len(matches))
                )
                continue

            item_index, item = matches[0]
            resolved.append((map_line, result_type, item_index, item))
            item_usage.setdefault(item_index, []).append(
                (map_line, result_type)
            )
            if item.get("itemmodule") != map_line.activity_type:
                issues[result_type].append(
                    _(
                        "La actividad Moodle %s no coincide con el tipo "
                        "mapeado (%s)."
                    )
                    % (activity_id, map_line.activity_type)
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

    def _irg_resolution_conflict(self, entry, map_lines):
        """Block structural conflicts before trying another HC edition."""
        items = entry.get("gradeitems", [])
        item_usage = {}
        for map_line in map_lines:
            activity_id = map_line.moodle_activity_id
            matches = self._irg_match_grade_items(items, activity_id)
            if len(matches) > 1:
                return _(
                    "La actividad Moodle %s tiene una resolución ambigua "
                    "(%s coincidencias por id/cmid/iteminstance)."
                ) % (activity_id, len(matches))
            if not matches:
                continue
            item_index, item = matches[0]
            if item.get("itemmodule") != map_line.activity_type:
                return _(
                    "La actividad Moodle %s no coincide con el tipo "
                    "mapeado (%s)."
                ) % (activity_id, map_line.activity_type)
            if item_index in item_usage:
                return _(
                    "La actividad Moodle %s tiene una resolución ambigua: "
                    "el mismo grade item se reutiliza."
                ) % activity_id
            item_usage[item_index] = map_line
        return False
