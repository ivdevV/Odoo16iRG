import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons.odoo_moodle_connector.models import utils as connector_utils
from . import grade_service
from . import utils

_logger = logging.getLogger(__name__)


class IrgMoodleGrade(models.Model):
    _name = 'irg.moodle.grade'
    _description = 'Nota sincronizada desde Moodle'
    _order = 'last_sync desc, id desc'
    _rec_name = 'moodle_fullname'

    student_id = fields.Many2one('op.student', string='Alumno', ondelete='set null')
    partner_id = fields.Many2one(
        'res.partner', string='Contacto',
        related='student_id.partner_id', store=True)
    subject_id = fields.Many2one('op.subject', string='Asignatura', ondelete='set null')
    subject_map_id = fields.Many2one(
        'irg.moodle.subject.map', string='Mapeo asignatura', ondelete='set null')

    moodle_course_id = fields.Integer(string='ID curso Moodle', index=True)
    moodle_user_id = fields.Integer(string='ID usuario Moodle', index=True)
    moodle_fullname = fields.Char(string='Nombre en Moodle')
    moodle_email = fields.Char(string='Correo en Moodle')

    grade_raw = fields.Char(string='Nota (bruta)')
    grade_numeric = fields.Float(string='Nota numérica')
    grade_max = fields.Float(string='Nota máxima')
    grade_percentage = fields.Char(string='Porcentaje')

    match_method = fields.Selection([
        ('manual', 'Manual'),
        ('md_id', 'Moodle-ID'),
        ('email', 'Correo'),
        ('name', 'Nombre'),
    ], string='Método de emparejamiento')
    state = fields.Selection([
        ('synced', 'Sincronizada'),
        ('unmatched_student', 'Alumno sin emparejar'),
    ], string='Estado', default='unmatched_student', index=True)
    last_sync = fields.Datetime(string='Última sincronización')

    _sql_constraints = [
        ('moodle_user_course_uniq',
         'unique(moodle_user_id, moodle_course_id)',
         'Ya existe una nota para este usuario y curso de Moodle.'),
    ]

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------
    @api.model
    def _sync_moodle_grades(self):
        """Core sync routine shared by the cron and the manual button.

        Returns a dict of counters {courses, synced, unmatched, skipped}.
        """
        credentials = connector_utils.get_moodle_credentials(self.env)
        if not credentials:
            _logger.warning('irg_moodle_grades_sync: sin credenciales Moodle, se omite.')
            return {'courses': 0, 'synced': 0, 'unmatched': 0, 'skipped': 0}

        service = grade_service.MoodleGradeService(credentials, self.env)
        student_model = self.env['op.student']
        maps = self.env['irg.moodle.subject.map'].search(
            [('active', '=', True), ('subject_id', '!=', False)])

        counters = {'courses': 0, 'synced': 0, 'unmatched': 0, 'skipped': 0}
        for smap in maps:
            grades = service.get_course_final_grades(smap.moodle_course_id)
            if not grades:
                counters['skipped'] += 1
                continue
            counters['courses'] += 1
            for entry in grades:
                student, method = student_model._irg_match_moodle_student(
                    entry['moodle_user_id'], entry.get('fullname'),
                    entry.get('email'))
                vals = {
                    'subject_id': smap.subject_id.id,
                    'subject_map_id': smap.id,
                    'moodle_course_id': smap.moodle_course_id,
                    'moodle_fullname': entry.get('fullname'),
                    'moodle_email': entry.get('email'),
                    'grade_raw': (str(entry['grade_raw'])
                                  if entry.get('grade_raw') is not None else False),
                    'grade_numeric': utils.parse_grade(entry.get('grade_numeric')) or 0.0,
                    'grade_max': entry.get('grade_max') or 0.0,
                    'grade_percentage': entry.get('grade_percentage'),
                    'last_sync': fields.Datetime.now(),
                }
                if student:
                    vals.update({
                        'student_id': student.id,
                        'match_method': method,
                        'state': 'synced',
                    })
                    counters['synced'] += 1
                else:
                    vals.update({
                        'student_id': False,
                        'match_method': False,
                        'state': 'unmatched_student',
                    })
                    counters['unmatched'] += 1
                self._upsert_grade(entry['moodle_user_id'],
                                   smap.moodle_course_id, vals)
        return counters

    @api.model
    def _upsert_grade(self, moodle_user_id, moodle_course_id, vals):
        """Create or update the grade row keyed by (user, course)."""
        record = self.search([
            ('moodle_user_id', '=', moodle_user_id),
            ('moodle_course_id', '=', moodle_course_id),
        ], limit=1)
        if record:
            record.write(vals)
        else:
            vals = dict(vals, moodle_user_id=moodle_user_id,
                        moodle_course_id=moodle_course_id)
            record = self.create(vals)
        return record

    @api.model
    def cron_sync_moodle_grades(self):
        """Scheduled entry point (ir.cron)."""
        counters = self._sync_moodle_grades()
        _logger.info(
            'irg_moodle_grades_sync cron: %s cursos, %s sincronizadas, '
            '%s sin emparejar, %s omitidos.',
            counters['courses'], counters['synced'],
            counters['unmatched'], counters['skipped'])
        return True

    def action_sync_now(self):
        """Manual button: run the sync and notify the user."""
        counters = self._sync_moodle_grades()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sincronización de notas Moodle'),
                'message': _(
                    '%s cursos, %s sincronizadas, %s sin emparejar, %s omitidos.') % (
                    counters['courses'], counters['synced'],
                    counters['unmatched'], counters['skipped']),
                'sticky': False,
            },
        }

    # ------------------------------------------------------------------
    # Manual match resolution
    # ------------------------------------------------------------------
    def action_confirm_match(self):
        """Persist the manually chosen student and mark the row as synced.

        Creates an irg.moodle.student.map so future syncs resolve this Moodle
        user automatically (match_method='manual').
        """
        student_map = self.env['irg.moodle.student.map']
        for rec in self:
            if not rec.student_id:
                raise UserError(_(
                    'Selecciona un alumno antes de confirmar el emparejamiento.'))
            if rec.moodle_user_id:
                existing = student_map.search(
                    [('moodle_user_id', '=', rec.moodle_user_id)], limit=1)
                map_vals = {
                    'moodle_fullname': rec.moodle_fullname,
                    'moodle_email': rec.moodle_email,
                    'student_id': rec.student_id.id,
                }
                if existing:
                    existing.write(map_vals)
                else:
                    student_map.create(dict(
                        map_vals, moodle_user_id=rec.moodle_user_id))
            rec.write({'match_method': 'manual', 'state': 'synced'})
        return True
