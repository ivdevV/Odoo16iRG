import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


# class OpBatch(models.Model):
#     _name = 'op.batch'
#     _description = "Asignaturas"


class OpBatch(models.Model):
    _inherit = 'op.batch'

    #slide_channel_id = fields.Many2one('slide.channel', string="Asignatura en Elearning")
    #subject_ids = fields.Many2many('op.subject', string='Subject(s)')
    subject_to_batch_ids = fields.One2many('op.subject.to.batch', 'batch_id', string='Asignaturas en lote')

    def _schedule_onl_subjects(self):
        for batch in self:
            is_onl = 'ONL' in (batch.code or '').upper() or 'ONL' in (batch.name or '').upper()
            if not is_onl or not batch.start_date:
                continue
            
            subjects = batch.subject_to_batch_ids.sorted(key=lambda r: r.id)
            current_date_from = batch.start_date
            for subject_line in subjects:
                subject_line.write({
                    'date_from': current_date_from,
                    'date_to': batch.end_date,
                })
                current_date_from = current_date_from + relativedelta(days=25)

    @api.model
    def create(self, vals):
        record = super(OpBatch, self).create(vals)
        if 'course_id' in vals:
            course = self.env['op.course'].browse(vals['course_id'])
            for subject in course.subject_ids:
                self.env['op.subject.to.batch'].create({
                    'batch_id': record.id,
                    'subject_id': subject.id,
                    'code': subject.code,
                })
        record._schedule_onl_subjects()
        return record

    def write(self, vals):
        if 'course_id' in vals:
            for record in self:
                record.subject_to_batch_ids.unlink()
                course = self.env['op.course'].browse(vals['course_id'])
                for subject in course.subject_ids:
                    self.env['op.subject.to.batch'].create({
                        'batch_id': record.id,
                        'subject_id': subject.id,
                        'code': subject.code,
                    })
        res = super(OpBatch, self).write(vals)
        if any(f in vals for f in ['course_id', 'start_date', 'end_date']):
            self._schedule_onl_subjects()
        return res
        

class OpSubjectToBatch(models.Model):
    _name = 'op.subject.to.batch'
    _description = "Asignaturas en lote"

    subject_id = fields.Many2one('op.subject', string="Asignatura")
    batch_id = fields.Many2one('op.batch', string="Lote")
    code = fields.Char(string="Código")
    date_to=fields.Date(string="Fecha de Fin")
    date_from=fields.Date(string="Fecha de Inicio")


    @api.onchange('date_from')
    def _onchange_date_from_in_range(self):
        if self.date_from:
            if self.date_from < self.batch_id.start_date:
                self.date_from = False
                return {
                    'warning': {
                        'title': "Error",
                        'message': "La fecha de inicio no puede ser anterior a la fecha de inicio del lote"
                    }
                }
        pass

    @api.onchange('date_to')
    def _onchange_date_to_in_range(self):
        if self.date_to:
            if self.date_to > self.batch_id.end_date:
                self.date_to = False
                return {
                    'warning': {
                        'title': "Error",
                        'message': "La fecha de fin no puede ser posterior a la fecha de fin del lote"
                    }
                }
        pass