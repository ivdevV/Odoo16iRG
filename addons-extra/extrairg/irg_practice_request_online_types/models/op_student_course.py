# -*- coding: utf-8 -*-

from odoo import api, fields, models

from .online_batch import irg_batch_code_is_online_master


class OpStudentCourse(models.Model):
    _inherit = 'op.student.course'

    irg_is_online_master_batch = fields.Boolean(
        compute='_compute_irg_is_online_master_batch',
        string='Máster online (prácticas)',
        help='True si el código de lote indica máster online. '
             'MONLHC y MONLPRS no cuentan.',
    )

    @api.depends('batch_id', 'batch_id.code')
    def _compute_irg_is_online_master_batch(self):
        for record in self:
            record.irg_is_online_master_batch = irg_batch_code_is_online_master(
                record.batch_id.code
            )
