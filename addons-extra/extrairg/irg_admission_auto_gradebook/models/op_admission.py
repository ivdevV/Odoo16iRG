# -*- coding: utf-8 -*-
import logging

from odoo import models, _

_logger = logging.getLogger(__name__)


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def enroll_student(self):
        """Override para crear la libreta de calificaciones automáticamente
        tras confirmar la matrícula.

        Se ejecuta el flujo estándar de OpenEduCat primero (super) y, una vez
        que la admisión ha pasado a estado 'done', se genera la libreta si el
        curso tiene la opción activada.
        """
        # Ejecutar el proceso estándar de matrícula (crea alumno, course_detail,
        # subject.registration y pone state='done').
        super().enroll_student()

        for record in self:
            # Solo actuar sobre admisiones que hayan quedado en estado 'done'
            if record.state != 'done':
                continue

            # Comprobar si el curso tiene habilitada la creación automática
            if not record.course_id or not record.course_id.auto_create_gradebook:
                _logger.debug(
                    'IRG Auto Gradebook: omitido para admisión %s '
                    '(auto_create_gradebook desactivado en el curso).',
                    record.id,
                )
                continue

            # Idempotencia: si ya existe una libreta para esta admisión, no crear otra
            existing = self.env['app.gradebook.student'].search(
                [('admission_id', '=', record.id)], limit=1
            )
            if existing:
                _logger.debug(
                    'IRG Auto Gradebook: ya existe la libreta %s para la '
                    'admisión %s. Se omite la creación.',
                    existing.id, record.id,
                )
                continue

            # Obtener asignaturas del curso según el filtro configurado
            subjects = record.course_id.subject_ids
            if record.course_id.auto_gradebook_subject_filter == 'compulsory':
                subjects = subjects.filtered(
                    lambda s: s.subject_type == 'compulsory'
                )

            # Crear la libreta.
            # sudo() justificado: enroll_student puede ejecutarse desde contextos
            # de suscripción o portal donde el usuario no tiene permisos directos
            # sobre app.gradebook.student (modelo de isep_gradebook).
            # El template 'Solo Examen' se asigna automáticamente a cada
            # app.gradebook.subject vía compute_gradebook_id (irg_gradebook_exam_as_final).
            gradebook = self.env['app.gradebook.student'].sudo().create({
                'admission_id': record.id,
            })

            _logger.info(
                'IRG Auto Gradebook: libreta %s creada para la admisión %s '
                '(alumno: %s, curso: %s).',
                gradebook.id,
                record.id,
                record.student_id.name,
                record.course_id.name,
            )

            # Poblar las líneas de asignatura y añadir 1 línea de examen por asignatura
            for subject in subjects:
                gb_subject = self.env['app.gradebook.subject'].sudo().create({
                    'gradebook_student_id': gradebook.id,
                    'op_subject_id': subject.id,
                })
                # Crear la evaluación de tipo examen automáticamente
                self.env['app.gradebook.result'].sudo().create({
                    'gradebook_subject_id': gb_subject.id,
                    'survey_type': 'exam',
                    'description': _('Evaluación'),
                    'scoring_total': 0.0,
                })

            _logger.info(
                'IRG Auto Gradebook: %s asignatura(s) añadida(s) a la '
                'libreta %s.',
                len(subjects),
                gradebook.id,
            )
