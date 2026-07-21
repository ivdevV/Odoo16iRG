from odoo import _
from odoo.addons.irg_moodle_grades_sync.models import constants
from odoo.addons.irg_moodle_grades_sync.models.grade_service import (
    MoodleGradeService,
)
from odoo.exceptions import UserError


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
        if err:
            raise UserError(
                _(
                    "No se pudieron obtener las notas de Moodle. "
                    "Inténtelo de nuevo más tarde."
                )
            )
        if not isinstance(payload, dict):
            raise UserError(_("La respuesta de notas de Moodle no es válida."))

        usergrades = payload.get('usergrades')
        if not isinstance(usergrades, list):
            raise UserError(_("La respuesta de notas de Moodle no es válida."))
        for usergrade in usergrades:
            if not isinstance(usergrade, dict):
                raise UserError(
                    _("La respuesta de notas de Moodle no es válida.")
                )
            gradeitems = usergrade.get('gradeitems')
            if not isinstance(gradeitems, list) or any(
                    not isinstance(item, dict) for item in gradeitems):
                raise UserError(
                    _("La respuesta de notas de Moodle no es válida.")
                )

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
        if not isinstance(enrolled, list):
            raise UserError(
                _("La respuesta de matriculados de Moodle no es válida.")
            )

        emails = {}
        for user in enrolled:
            if not isinstance(user, dict):
                continue
            user_id = user.get('id')
            if user_id:
                emails[user_id] = (user.get('email') or '').strip()
        return usergrades, emails
