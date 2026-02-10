import logging
from datetime import date

from odoo import models, api

_logger = logging.getLogger(__name__)


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    # ------------------------------------------------------------------
    # Botón "Auto-Asignaturas": agrega verificación de precedencia
    # ------------------------------------------------------------------
    def auto_enroll_student(self):
        """Sobreescribe para respetar la precedencia de asignaturas.
        Si una asignatura tiene parent_subject_id, solo se inscribe al alumno
        cuando el padre ya fue completado."""
        today = date.today()
        for record in self:
            if record.state != 'done' or not record.batch_id:
                continue

            for subject_batch in record.batch_id.subject_to_batch_ids:
                subject = subject_batch.subject_id
                if not subject.slide_channel_id:
                    continue
                if not subject_batch.date_from or not subject_batch.date_to:
                    continue

                # --- Verificar precedencia ---
                if subject.parent_subject_id:
                    parent_cp = self.env['slide.channel.partner'].sudo().search([
                        ('partner_id', '=', record.partner_id.id),
                        ('op_subject_id', '=', subject.parent_subject_id.id),
                        ('admission_id', '=', record.id),
                        ('active', '=', True),
                    ], limit=1)
                    if not parent_cp or not parent_cp.completed:
                        continue

                channel_partners = self.env['slide.channel.partner'].search([
                    ('partner_id', '=', record.partner_id.id),
                    ('channel_id', '=', subject.slide_channel_id.id),
                    ('batch_id', '=', record.batch_id.id),
                ])

                if subject_batch.date_from <= today <= subject_batch.date_to:
                    if channel_partners:
                        channel_partners.write({
                            'active': True,
                            'course_id': record.course_id.id,
                            'register_id': record.register_id.id,
                            'admission_id': record.id,
                            'date_from': subject_batch.date_from,
                            'date_to': subject_batch.date_to,
                        })
                    else:
                        self.env['slide.channel.partner'].create({
                            'active': True,
                            'channel_id': subject.slide_channel_id.id,
                            'partner_id': record.partner_id.id,
                            'course_id': record.course_id.id,
                            'batch_id': record.batch_id.id,
                            'date_from': subject_batch.date_from,
                            'date_to': subject_batch.date_to,
                            'op_subject_id': subject.id,
                            'register_id': record.register_id.id,
                            'admission_id': record.id,
                        })

                elif today > subject_batch.date_to and channel_partners:
                    channel_partners.write({'active': False})

    # ------------------------------------------------------------------
    # Cron diario: agrega filtro de modalidad, precedencia y batch_id
    # ------------------------------------------------------------------
    def cron_auto_enroll_student(self):
        """Sobreescribe el cron para:
        - Omitir admisiones en modalidad 'manual'.
        - Verificar precedencia antes de inscribir.
        - Filtrar por batch_id al buscar registros existentes.
        """
        today = date.today()
        admissions = self.search([('state', '=', 'done'), ('batch_id', '!=', False)])

        for record in admissions:
            # Solo procesar admisiones en modalidad automática
            if hasattr(record, 'modality') and record.modality == 'manual':
                continue

            for subject_batch in record.batch_id.subject_to_batch_ids:
                subject = subject_batch.subject_id
                if not subject.slide_channel_id:
                    continue
                if not subject_batch.date_from or not subject_batch.date_to:
                    continue

                # --- Verificar precedencia ---
                if subject.parent_subject_id:
                    parent_cp = self.env['slide.channel.partner'].sudo().search([
                        ('partner_id', '=', record.partner_id.id),
                        ('op_subject_id', '=', subject.parent_subject_id.id),
                        ('admission_id', '=', record.id),
                        ('active', '=', True),
                    ], limit=1)
                    if not parent_cp or not parent_cp.completed:
                        continue

                # Buscar registros activos e inactivos, filtrando por batch
                channel_partner = self.env['slide.channel.partner'].sudo().search([
                    ('partner_id', '=', record.partner_id.id),
                    ('channel_id', '=', subject.slide_channel_id.id),
                    ('batch_id', '=', record.batch_id.id),
                    '|',
                    ('active', '=', True),
                    ('active', '=', False),
                ], order='create_date ASC', limit=1)

                if subject_batch.date_from <= today <= subject_batch.date_to:
                    if channel_partner:
                        channel_partner.write({
                            'active': True,
                            'course_id': record.course_id.id,
                            'register_id': record.register_id.id,
                            'admission_id': record.id,
                            'batch_id': record.batch_id.id,
                            'date_from': subject_batch.date_from,
                            'date_to': subject_batch.date_to,
                        })
                    else:
                        self.env['slide.channel.partner'].sudo().create({
                            'active': True,
                            'channel_id': subject.slide_channel_id.id,
                            'partner_id': record.partner_id.id,
                            'course_id': record.course_id.id,
                            'batch_id': record.batch_id.id,
                            'date_from': subject_batch.date_from,
                            'date_to': subject_batch.date_to,
                            'op_subject_id': subject.id,
                            'register_id': record.register_id.id,
                            'admission_id': record.id,
                        })

                elif today > subject_batch.date_to and channel_partner:
                    channel_partner.write({'active': False})
