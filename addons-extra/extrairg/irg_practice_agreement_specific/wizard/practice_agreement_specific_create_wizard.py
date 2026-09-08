# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError

DAY_LABELS = (
    ('monday', 'Lunes'),
    ('tuesday', 'Martes'),
    ('wednesday', 'Miércoles'),
    ('thursday', 'Jueves'),
    ('friday', 'Viernes'),
    ('saturday', 'Sábado'),
    ('sunday', 'Domingo'),
)


def _float_to_hour(value):
    if not value:
        return '00:00'
    hours = int(value)
    minutes = int(round((value - hours) * 60))
    if minutes >= 60:
        hours += 1
        minutes = 0
    return '%d:%02d' % (hours, minutes)


class PracticeAgreementSpecificCreateWizard(models.TransientModel):
    _name = 'irg.practice.agreement.specific.create.wizard'
    _description = 'Crear Convenio Específico'

    practice_request_id = fields.Many2one(
        'practice.request',
        string='Solicitud de prácticas',
        required=True,
        ondelete='cascade',
    )
    agreement_type = fields.Selection(
        [
            ('especifico_internacional', 'Convenio Específico Internacional'),
            ('especifico_nacional', 'Convenio Específico Nacional'),
        ],
        string='Tipo de convenio',
        required=True,
        default='especifico_internacional',
    )
    student_proposed_activities = fields.Text(
        string='Actividades propuestas por el alumno',
    )

    def _snapshot_vals(self, request):
        days = []
        schedule = ''
        for key, label in DAY_LABELS:
            start = getattr(request, '%s_available_start_time' % key, 0.0)
            end = getattr(request, '%s_available_end_time' % key, 0.0)
            if start or end:
                days.append(label)
                if not schedule and start and end:
                    schedule = '%s a %s horas' % (
                        _float_to_hour(start),
                        _float_to_hour(end),
                    )
        student = request.op_student_id or request.course_id.student_id
        partner = student.partner_id if student else False
        course = request.op_student_course_course_id or request.course_id.course_id
        modality = ''
        if request.practice_center_type_id:
            modality = request.practice_center_type_id.display_name or ''
        return {
            'practice_center_id': request.practice_center_id.id,
            'practice_request_id': request.id,
            'agreement_type': self.agreement_type,
            'student_name': request.name,
            'student_email': request.email,
            'student_vat': partner.vat if partner else False,
            'course_name': course.name if course else False,
            'start_date': request.start_date,
            'final_date': request.final_date,
            'total_hours': request.total_hours,
            'practice_days': ', '.join(days),
            'schedule_hours': schedule,
            'modality': modality,
            'tutor_name': request.tutor_id.name if request.tutor_id else False,
            'tutor_vat': request.tutor_id.vat if request.tutor_id else False,
            'student_proposed_activities': self.student_proposed_activities,
        }

    def action_create_agreement(self):
        self.ensure_one()
        request = self.practice_request_id
        if not request.practice_center_id:
            raise UserError(
                _('La solicitud debe tener un centro de prácticas asignado.')
            )
        agreement = self.env['practice.agreement'].create(
            self._snapshot_vals(request)
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Convenio'),
            'res_model': 'practice.agreement',
            'res_id': agreement.id,
            'view_mode': 'form',
            'target': 'current',
        }
