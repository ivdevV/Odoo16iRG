import logging

from odoo.addons.irg_moodle_grades_sync.models import constants
from odoo.addons.irg_moodle_grades_sync.models.grade_service import (
    MoodleGradeService,
)

_logger = logging.getLogger(__name__)


class GradebookMoodleService(MoodleGradeService):
    """Extiende el servicio de notas para exponer los grade items
    individuales de un curso (no solo el total itemtype=='course')."""

    def get_user_grade_items(self, moodle_course_id):
        """Devuelve (usergrades, emails) de un curso Moodle.

        usergrades: lista cruda de gradereport_user_get_grade_items
          [{'userid', 'userfullname', 'gradeitems': [{'id', 'cmid',
            'itemname', 'itemmodule', 'graderaw', 'grademax', ...}]}]
        emails: {moodle_user_id: email} del endpoint de matrícula.
        """
        payload, err = self._call(
            constants.MDL_GRADE_GET_ITEMS_FUNC,
            {'courseid': moodle_course_id})
        if err or not isinstance(payload, dict):
            return [], {}
        emails = self.get_enrolled_emails(moodle_course_id)
        return payload.get('usergrades', []), emails
