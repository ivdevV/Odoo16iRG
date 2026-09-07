import logging
import re

from psycopg2 import IntegrityError

from odoo import api, fields, models


_logger = logging.getLogger(__name__)
_TFM_THESIS_UNIQUE_CONSTRAINT = 'irg_tfm_tesis_course_unique'
_BATCH_CODE_RE = re.compile(r'(HC|ONL)(\d{4})', re.IGNORECASE)
_TFM_CRON_CURSOR_PARAM = 'irg_tfm_convocatorias.activation_cursor'
_TFM_CRON_BATCH_SIZE = 500


def irg_parse_tfm_batch_eligibility(code):
    """Return the eligible modality and YYMM extracted from a batch code.

    The parser is deliberately pure so eligibility rules can be covered without
    coupling them to the OpenEduCat ORM.
    """
    if not code or 'PRS' in code.upper():
        return False
    match = _BATCH_CODE_RE.search(code)
    if not match:
        return False
    modality = match.group(1).upper()
    yymm = int(match.group(2))
    month = yymm % 100
    if not 1 <= month <= 12:
        return False
    if 'MONLHC' in code.upper():
        minimum = 2601
    elif modality == 'HC':
        minimum = 2511
    else:
        minimum = 2602
    return (modality, yymm) if yymm >= minimum else False


class OpStudentCourse(models.Model):
    _inherit = 'op.student.course'

    _IRG_TFM_MEMBERSHIP_TRIGGER_FIELDS = {'student_id', 'course_id', 'batch_id'}

    def _irg_tfm_completion_percentage(self):
        """Read the real, non-stored course progress without trusting cache."""
        self.ensure_one()
        enrollment = self.sudo()
        enrollment.invalidate_recordset(['completion_porc'])
        return float(enrollment.completion_porc or 0.0)

    def _irg_is_tfm_eligible(self):
        self.ensure_one()
        return bool(
            self.course_id.activate_tesis
            and self._irg_tfm_completion_percentage() >= 50.0
            and irg_parse_tfm_batch_eligibility(self.batch_id.code)
        )

    def _irg_ensure_tfm_record(self):
        """Create exactly one thesis record for an eligible enrollment.

        PostgreSQL is the final concurrency guard. Only that expected unique
        violation is absorbed; all other database errors remain visible.
        """
        self.ensure_one()
        Thesis = self.env['tesis.model']
        existing = Thesis.search([('course_id', '=', self.id)], limit=1)
        if existing or not self._irg_is_tfm_eligible():
            return existing
        try:
            with self.env.cr.savepoint():
                return Thesis.with_context(irg_tfm_auto_activation=True).create({
                    'name': self.student_id.name,
                    'email': self.student_id.email,
                    'course_id': self.id,
                    'state': 'draft',
                    'irg_tfm_activated_at': fields.Datetime.now(),
                })
        except IntegrityError as exc:
            if getattr(exc.diag, 'constraint_name', None) != _TFM_THESIS_UNIQUE_CONSTRAINT:
                raise
            _logger.info('TFM thesis already activated concurrently for enrollment %s', self.id)
            return Thesis.search([('course_id', '=', self.id)], limit=1)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._irg_ensure_tfm_record()
        return records

    def write(self, vals):
        result = super().write(vals)
        for record in self:
            record._irg_ensure_tfm_record()
        if self._IRG_TFM_MEMBERSHIP_TRIGGER_FIELDS.intersection(vals):
            if self.env.user.has_group('base.group_user'):
                theses = self.env['tesis.model'].search([
                    ('course_id', 'in', self.ids),
                ])
                for thesis in theses:
                    thesis._irg_reconcile_tfm_membership()
        return result

    @api.model
    def _cron_irg_ensure_tfm_records(self):
        """Process one bounded page and persist its cursor for later runs."""
        Param = self.env['ir.config_parameter'].sudo()
        try:
            last_id = int(Param.get_param(_TFM_CRON_CURSOR_PARAM, '0'))
        except (TypeError, ValueError):
            last_id = 0
        try:
            batch_size = int(self.env.context.get(
                'irg_tfm_cron_batch_size', _TFM_CRON_BATCH_SIZE,
            ))
        except (TypeError, ValueError):
            batch_size = _TFM_CRON_BATCH_SIZE
        batch_size = min(max(batch_size, 1), _TFM_CRON_BATCH_SIZE)
        domain = [
            ('id', '>', last_id),
            ('course_id.activate_tesis', '=', True),
        ]
        candidates = self.search(domain, order='id', limit=batch_size)
        if not candidates:
            Param.set_param(_TFM_CRON_CURSOR_PARAM, '0')
            return True
        for record in candidates:
            record._irg_ensure_tfm_record()
        Param.set_param(_TFM_CRON_CURSOR_PARAM, str(candidates[-1].id))
        return True
