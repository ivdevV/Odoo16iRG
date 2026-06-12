# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def state_to_done(self):
        for rec in self:
            if not rec.gradebook_id:
                raise UserError(_('"Calificaciones template" es obligatorio.'))
            for subject in rec.gradebook_subject_ids:
                code = subject.op_subject_id.code
                if code and code.upper().startswith('NLEX'):
                    continue
                
                gradebook = subject._get_gradebook_info(subject)
                if gradebook:
                    qty_examn = len(subject.gradebook_result_ids.filtered(lambda x: x.survey_type == 'exam'))
                    if gradebook['exam']['qty'] != qty_examn and subject.show_exam:
                        raise UserError(_('%s: Tiene %s evaluaciones de tipo "Examen" pero necesita %s.') % (subject.name, qty_examn, gradebook['exam']['qty']))
                    
                    qty_assignment = len(subject.gradebook_result_ids.filtered(lambda x: x.survey_type == 'assignment'))
                    if gradebook['assignment']['qty'] != qty_assignment and subject.show_assignment:
                        raise UserError(_('%s: Tiene %s evaluaciones de tipo "Asignación" pero necesita %s.') % (subject.name, qty_assignment, gradebook['exam']['qty']))

                    qty_foro = len(subject.gradebook_result_ids.filtered(lambda x: x.survey_type == 'interaction'))
                    if qty_foro != 1 and subject.show_interaction:
                        raise UserError(_('%s: Debe tener 1 evaluacion de tipo "Interaccion".') % subject.name)

                    qty_foro = len(subject.gradebook_result_ids.filtered(lambda x: x.survey_type == 'foro'))
                    if qty_foro != 1 and subject.show_foro:
                        raise UserError(_('%s: Debe tener 1 evaluacion de tipo "Foro".') % subject.name)
            
            rec.state = 'done'

    @api.depends('gradebook_subject_ids.final_subject_note')
    def _amount_prod_final(self):
        for order in self:
            compulsory_notes = []
            for line in order.gradebook_subject_ids:
                code = line.op_subject_id.code
                if code and code.upper().startswith('NLEX'):
                    continue
                if line.op_subject_id.subject_type == 'compulsory' and line.final_subject_note is not None:
                    compulsory_notes.append(line.final_subject_note)
            order.total_final = sum(compulsory_notes) / len(compulsory_notes) if compulsory_notes else 0.0

    @api.depends('student_id', 'gradebook_subject_ids', 'gradebook_subject_ids.final_subject_note', 
                 'gradebook_subject_ids.op_subject_id', 'gradebook_subject_ids.op_subject_id.subject_type',
                 'gradebook_subject_ids.op_subject_id.code')
    def compute_avg_score(self):
        for rec in self:
            subject_ids = rec.gradebook_subject_ids.filtered(
                lambda r: r.op_subject_id.subject_type == 'compulsory' and 
                          not (r.op_subject_id.code and r.op_subject_id.code.upper().startswith('NLEX'))
            )
            sum_score = 0.0
            s_index = 0
            for subject_id in subject_ids:
                sum_score += subject_id.final_subject_note
                s_index += 1
                 
            rec.avg_score = sum_score / s_index if s_index > 0 else 0.0

    def action_export_to_dec(self):
        new_records = self.env['dec.document']
        for record in self:
            new_lines = self.env['dec.asignatura']
            responsable_id = self.env.company.dec_responsable_id
            if not responsable_id:
                raise ValidationError(_('Se requiere configurar el responsable DEC en ajustes.'))
            
            # Exclude compulsory subjects whose code starts with 'NLEX'
            total_subjects = record.course_id.subject_ids.filtered(
                lambda s: s.subject_type == 'compulsory' and not (s.code and s.code.upper().startswith('NLEX'))
            )
            total = len(total_subjects)
            total_creditos = sum(total_subjects.mapped('credit_point'))
            
            certificate_vals = {
                'responsable_id': responsable_id.id or False,
                'ides_ipes': record.course_id.institute_key,
                'id_campus': record.course_id.career_key,
                'rvoe': record.course_id.rvoe_number,
                'fecha_rvoe': record.course_id.rvoe_date,
                'curp_alumno': record.student_id.partner_id.l10n_mx_edi_curp,
                'alumno_nombre': ' '.join(filter(None, [record.student_id.first_name, record.student_id.middle_name])),
                'primer_apellido': record.student_id.last_name and record.student_id.last_name.split()[0],
                'segundo_apellido': record.student_id.last_name and len(record.student_id.last_name.split()) > 1 and record.student_id.last_name.split()[1] or '',
                'fecha_nacimiento': record.student_id.birth_date,
                'id_genero': record.student_id.gender == 'f' and '250' or '251',
                'programa_estudio': record.course_id.id_carrera,
                'calificacion_minima': record.course_id.calificacion_minima,
                'calificacion_maxima': record.course_id.calificacion_maxima,
                'calificacion_minima_aprobatoria': record.course_id.calificacion_minima_aprobatoria,
                'programa_estudio_tipo': '93',
                'total': total,
                'total_creditos': total_creditos,
                'clave_plan': '2020',
                'nivel_estudios': '82',
                'numero_control': record.admission_id.application_number,
                'id_tipo_certificacion': record.state == 'done' and '79' or '80',
            }
            new_certificate = new_records.create(certificate_vals)
            
            for subject in record.gradebook_subject_ids.filtered(
                lambda s: s.op_subject_id.subject_type == 'compulsory' and not (s.op_subject_id.code and s.op_subject_id.code.upper().startswith('NLEX'))
            ):
                new_line = new_lines.create({
                    'dec_id': new_certificate.id,
                    'clave_asignatura': subject.op_subject_id.code,
                    'calificacion': subject.final_subject_note,
                    'creditos': 1,
                })
            new_records |= new_certificate

        return {
            'name': _('Certificados DEC SEP'),
            'res_model': 'dec.document',
            'view_mode': 'tree,form',
            'context': {
                'active_model': 'dec.document',
                'active_ids': new_records.ids,
            },
            'target': 'self',
            'type': 'ir.actions.act_window',
        }
