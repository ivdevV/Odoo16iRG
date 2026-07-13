import logging

from psycopg2 import IntegrityError

from odoo import models


_logger = logging.getLogger(__name__)

_UNIQUE_INDEX = 'irg_scp_active_partner_channel_batch_uniq'


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def auto_enroll_student(self):
        for record in self:
            try:
                with self.env.cr.savepoint():
                    super(OpAdmission, record).auto_enroll_student()
            except IntegrityError as exc:
                if exc.diag.constraint_name != _UNIQUE_INDEX:
                    raise
                _logger.info(
                    'Concurrent auto-enroll membership already exists for admission %s',
                    record.id,
                )
        return True
