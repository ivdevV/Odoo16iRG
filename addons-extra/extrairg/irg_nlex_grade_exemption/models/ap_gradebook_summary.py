# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class AppisepGradebookSummary(models.Model):
    _inherit = 'appisep.gradebook.summary'

    def determine_current_quarter(self):
        try:
            start_date = self.batch_id.start_date
            end_date = self.batch_id.end_date
            final_notes = []
            current_quarter = None

            if not start_date or not end_date:
                return final_notes

            current_date = datetime.now().date()
            
            if start_date <= current_date <= end_date:
                quarters = []
                current_start = start_date
                counter = 1

                while current_start <= end_date:
                    q_end = current_start + relativedelta(months=4, days=-1)

                    if q_end > end_date:
                        q_end = end_date
                    
                    quarters.append({
                        'number': counter,
                        'start': current_start,
                        'end': q_end,
                        'active': q_end >= current_date 
                    })
                    
                    current_start = q_end + relativedelta(days=1)
                    counter += 1

                for q in quarters:
                    if q['start'] <= current_date <= q['end']:
                        current_quarter = q
                        break

                if current_quarter:
                    description = f"Cuatrimestre {current_quarter['number']}: {current_quarter['start'].strftime('%d/%m/%Y')} - {current_quarter['end'].strftime('%d/%m/%Y')}"
                    
                    # Exclude exempt subjects (code contains 'EX')
                    slide_channels = self.env['slide.channel.partner'].search([
                        ('active', '=', True),
                        ('partner_id', '=', self.student_id.id),
                        ('op_subject_id.subject_type', '=', 'compulsory'),
                        ('batch_id', '=', self.batch_id.id),
                        ('write_date', '>=', current_quarter['start']),
                        ('write_date', '<=', current_quarter['end'])
                    ]).filtered(lambda r: not r.op_subject_id.irg_is_grade_exempt())
                    
                    current_quarter_ids = slide_channels.op_subject_id.ids
                    
                    if current_quarter_ids:
                        subject_notes = self.env['app.gradebook.subject'].search([
                            ('op_subject_id', 'in', current_quarter_ids),
                            ('admission_id', '=', self.admision_id.id),
                            ('partner_id', '=', self.student_id.id)
                        ])                    
                        final_notes = subject_notes.mapped('final_subject_note')
                        average = sum(final_notes) / len(final_notes) if final_notes else 0.0
                        self.write({
                            'total_marks': average,
                            'description': description,
                            'mail_send': False
                        })
            
            return final_notes

        except Exception as e:
            _logger.error(f"Error en registro {self.id}: {str(e)}")
            return []
