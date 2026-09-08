# -*- coding: utf-8 -*-
import base64

from odoo import api, models


class IrgDiplomadoRegistry(models.Model):
    _inherit = 'irg.diplomado.registry'

    @api.model
    def _irg_celebration_start_from_batch(self, batch):
        if not batch:
            return False
        return batch.date_start_class or batch.start_date

    def _irg_get_celebration_batch(self):
        self.ensure_one()
        lines = self.env['op.student.course'].search([
            ('student_id', '=', self.student_id.id),
            ('course_id', '=', self.course_id.id),
        ], order='id desc')
        finished = lines.filtered(lambda line: line.state == 'finished')
        line = finished[:1] or lines[:1]
        if line and line.batch_id:
            return line.batch_id
        if 'app.gradebook.student' not in self.env:
            return self.env['op.batch']
        gradebook = self.env['app.gradebook.student'].search([
            ('student_id', '=', self.student_id.id),
            ('course_id', '=', self.course_id.id),
        ], order='id desc', limit=1)
        return gradebook.batch_id if gradebook and gradebook.batch_id else self.env['op.batch']

    def _irg_resolved_celebration_start(self):
        self.ensure_one()
        batch = self._irg_get_celebration_batch()
        if not batch:
            return self.start_date
        return self._irg_celebration_start_from_batch(batch) or self.start_date

    def _irg_should_refresh_on_download(self):
        """Refresh the stored PDF on portal download only when it is missing
        or the stored start_date is stale against the live class start.

        Records with an empty start_date keep the existing attachment. That
        matches historical portal tests and does not apply to issued diplomas,
        which always persist a start_date.
        """
        self.ensure_one()
        if not self.attachment_id or not self.attachment_id.datas:
            return True
        live_start = self._irg_resolved_celebration_start()
        return bool(self.start_date and live_start and self.start_date != live_start)

    def _irg_attachment_belongs_to_registry(self, attachment):
        self.ensure_one()
        return bool(
            attachment
            and attachment.res_model == 'irg.diplomado.registry'
            and attachment.res_id == self.id
        )

    def _irg_store_pdf(self, pdf_content):
        self.ensure_one()
        payload = base64.b64encode(pdf_content)
        attachment_name = 'Diplomado_%s.pdf' % self.student_name.replace(' ', '_')
        attachment = self.attachment_id
        if self._irg_attachment_belongs_to_registry(attachment):
            attachment.write({
                'datas': payload,
                'name': attachment_name,
                'mimetype': 'application/pdf',
            })
        else:
            attachment = self.env['ir.attachment'].create({
                'name': attachment_name,
                'type': 'binary',
                'datas': payload,
                'res_model': 'irg.diplomado.registry',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            self.attachment_id = attachment

    def action_reprint(self):
        self.ensure_one()
        live_start = self._irg_resolved_celebration_start()
        data = self._get_diplomado_pdf_data()
        if live_start:
            data['start_date'] = live_start.strftime('%d/%m/%Y')
        pdf_content = self.env['report.irg_generacion_diplomados.diplomado_pdf'].generate_diplomado_pdf(
            data
        )
        vals = {}
        if live_start and self.start_date != live_start:
            vals['start_date'] = live_start
        if vals:
            self.write(vals)
        self._irg_store_pdf(pdf_content)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % self.attachment_id.id,
            'target': 'self',
        }
