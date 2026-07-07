import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# odoo_moodle_connector helper to fetch the shared moodle.credentials record.
from odoo.addons.odoo_moodle_connector.models import utils as connector_utils
from . import grade_service

_logger = logging.getLogger(__name__)


class IrgMoodleSubjectMap(models.Model):
    _name = 'irg.moodle.subject.map'
    _description = 'Mapeo curso Moodle -> asignatura Odoo'
    _order = 'subject_id, moodle_course_name'

    moodle_course_id = fields.Integer(
        string='ID curso Moodle', required=True, index=True)
    moodle_course_name = fields.Char(string='Nombre curso Moodle')
    moodle_course_shortname = fields.Char(string='Nombre corto Moodle')
    subject_id = fields.Many2one(
        'op.subject', string='Asignatura Odoo', ondelete='cascade')
    course_id = fields.Many2one('op.course', string='Curso Odoo')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('moodle_course_id_uniq', 'unique(moodle_course_id)',
         'Ya existe un mapeo para este curso de Moodle.'),
    ]

    @api.model
    def action_import_moodle_courses(self):
        """Fetch the Moodle course catalogue and create draft (unmapped) rows.

        Existing rows are refreshed (name/shortname) but never overwrite the
        subject the admin already linked. New courses appear with an empty
        subject_id so the admin can map them once.
        """
        credentials = connector_utils.get_moodle_credentials(self.env)
        if not credentials:
            raise UserError(_(
                'No hay credenciales de Moodle configuradas. '
                'Configúralas en el módulo Odoo Moodle Connector.'))
        service = grade_service.MoodleGradeService(credentials, self.env)
        courses = service.get_all_courses()
        if not courses:
            raise UserError(_(
                'No se han recibido cursos desde Moodle. '
                'Revisa el token y que el WS core_course_get_courses esté habilitado.'))
        created = 0
        for course in courses:
            existing = self.with_context(active_test=False).search(
                [('moodle_course_id', '=', course['id'])], limit=1)
            vals = {
                'moodle_course_name': course['fullname'],
                'moodle_course_shortname': course['shortname'],
            }
            if existing:
                existing.write(vals)
            else:
                vals['moodle_course_id'] = course['id']
                self.create(vals)
                created += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cursos Moodle importados'),
                'message': _('%s cursos nuevos, %s en total.') % (
                    created, len(courses)),
                'sticky': False,
            },
        }
