from odoo import _
from odoo.addons.irg_moodle_grades_sync.models import constants
from odoo.addons.irg_moodle_grades_sync.models.grade_service import (
    MoodleGradeService,
)
from odoo.exceptions import UserError


class GradebookMoodleService(MoodleGradeService):
    """Extiende el servicio de notas para exponer los grade items
    individuales de un curso (no solo el total itemtype=='course')."""

    @staticmethod
    def _raise_invalid_response():
        raise UserError(_("La respuesta recibida de Moodle no es válida."))

    @staticmethod
    def _is_positive_int(value):
        return type(value) is int and value > 0

    @staticmethod
    def _is_optional_int(value):
        return value is None or type(value) is int

    @staticmethod
    def _is_optional_string(value):
        return value is None or isinstance(value, str)

    @staticmethod
    def _is_grade_scalar(value):
        return value is None or type(value) in (int, float, str)

    @classmethod
    def _validate_grade_payload(cls, payload):
        if not isinstance(payload, dict):
            cls._raise_invalid_response()
        usergrades = payload.get('usergrades')
        if not isinstance(usergrades, list):
            cls._raise_invalid_response()

        for usergrade in usergrades:
            if not isinstance(usergrade, dict):
                cls._raise_invalid_response()
            if not cls._is_positive_int(usergrade.get('userid')):
                cls._raise_invalid_response()
            if not cls._is_optional_string(usergrade.get('userfullname')):
                cls._raise_invalid_response()

            gradeitems = usergrade.get('gradeitems')
            if not isinstance(gradeitems, list):
                cls._raise_invalid_response()
            for item in gradeitems:
                if not isinstance(item, dict):
                    cls._raise_invalid_response()
                if not all(
                        cls._is_optional_int(item.get(field_name))
                        for field_name in ('id', 'cmid')):
                    cls._raise_invalid_response()
                if not all(
                        cls._is_optional_string(item.get(field_name))
                        for field_name in ('itemname', 'itemmodule')):
                    cls._raise_invalid_response()
                if not all(
                        cls._is_grade_scalar(item.get(field_name))
                        for field_name in ('graderaw', 'grademax')):
                    cls._raise_invalid_response()
        return usergrades

    @classmethod
    def _validate_enrolled_payload(cls, payload):
        if not isinstance(payload, list):
            cls._raise_invalid_response()
        for user in payload:
            if not isinstance(user, dict):
                cls._raise_invalid_response()
            if not cls._is_positive_int(user.get('id')):
                cls._raise_invalid_response()
            if not cls._is_optional_string(user.get('email')):
                cls._raise_invalid_response()
        return payload

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
        if err:
            raise UserError(
                _(
                    "No se pudieron obtener las notas de Moodle. "
                    "Inténtelo de nuevo más tarde."
                )
            )
        usergrades = self._validate_grade_payload(payload)

        enrolled, enrolled_err = self._call(
            constants.MDL_ENROL_GET_USERS_FUNC,
            {'courseid': moodle_course_id})
        if enrolled_err:
            raise UserError(
                _(
                    "No se pudieron obtener los matriculados de Moodle. "
                    "Inténtelo de nuevo más tarde."
                )
            )
        enrolled = self._validate_enrolled_payload(enrolled)

        emails = {}
        for user in enrolled:
            user_id = user.get('id')
            emails[user_id] = (user.get('email') or '').strip()
        return usergrades, emails
