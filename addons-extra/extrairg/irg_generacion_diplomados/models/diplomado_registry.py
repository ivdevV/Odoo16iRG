# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class IrgDiplomadoRegistry(models.Model):
    _name = 'irg.diplomado.registry'
    _description = 'Registro de Diplomados'
    _order = 'issue_date desc, id desc'

    name = fields.Char(
        string='Número de Registro',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help=_("Número de registro único del diplomado.")
    )
    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        required=True,
        ondelete='restrict',
        help=_("Estudiante al que se le otorga el diplomado.")
    )
    student_name = fields.Char(
        string='Nombre del Alumno',
        required=True,
        help=_("Nombre completo del alumno en el momento de la expedición.")
    )
    course_id = fields.Many2one(
        'op.course',
        string='Curso',
        required=True,
        ondelete='restrict',
        help=_("Curso/Diplomado cursado.")
    )
    diplomado_name = fields.Char(
        string='Nombre del Diplomado',
        required=True,
        help=_("Nombre descriptivo del diplomado impreso.")
    )
    start_date = fields.Date(
        string='Fecha de Inicio',
        help=_("Fecha de inicio del curso.")
    )
    end_date = fields.Date(
        string='Fecha de Fin',
        help=_("Fecha de finalización del curso.")
    )
    duration_hours = fields.Integer(
        string='Duración (Horas)',
        help=_("Duración total del diplomado en horas.")
    )
    duration_ects = fields.Float(
        string='Créditos ECTS',
        help=_("Créditos ECTS asignados al diplomado.")
    )
    issue_date = fields.Date(
        string='Fecha de Expedición',
        default=fields.Date.context_today,
        required=True,
        help=_("Fecha en la que se expide/imprime el diplomado.")
    )
    diploma_type = fields.Selection([
        ('digital', 'Digital'),
        ('physical', 'Físico')
    ], string='Tipo de Diploma', required=True, default='digital', help=_("Tipo de diploma generado."))
    
    subjects_presencial = fields.Text(
        string='Asignaturas Presenciales',
        help=_("Listado de asignaturas presenciales que figurarán en el reverso.")
    )
    subjects_online = fields.Text(
        string='Asignaturas Online',
        help=_("Listado de asignaturas online que figurarán en el reverso.")
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Archivo PDF',
        help=_("Archivo PDF adjunto que contiene el diplomado generado.")
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('irg.diplomado.registry') or _('New')
        return super(IrgDiplomadoRegistry, self).create(vals)

    def action_reprint(self):
        self.ensure_one()
        if not self.attachment_id:
            # Regenerar el PDF si no existiera (por ejemplo, registros creados anteriormente)
            start_date_str = self.start_date.strftime('%d/%m/%Y') if self.start_date else ''
            end_date_str = self.end_date.strftime('%d/%m/%Y') if self.end_date else ''
            issue_date_str = self.issue_date.strftime('%d/%m/%Y') if self.issue_date else ''

            # Calcular la URL del QR de forma idéntica a diplomas convencionales
            from urllib.parse import urlencode
            query_params = {'id': self.name}
            if 'op.sign_certificate' in self.env:
                stamp_payload = {
                    'registry_number': self.name,
                    'student_name': self.student_name,
                    'course_name_es': self.diplomado_name,
                    'course_name_cat': self.diplomado_name,
                    'issue_date': str(self.issue_date),
                    'diploma_type': self.diploma_type,
                }
                stamp_data = self.env['op.sign_certificate'].sudo().stamp_data(stamp_payload, student=self.student_id) or {}
                if stamp_data.get('stamp') and stamp_data.get('data_str') and stamp_data.get('certificate_id'):
                    query_params.update({
                        'stamp': stamp_data.get('stamp'),
                        'data_str': stamp_data.get('data_str'),
                        'certificate_id': stamp_data.get('certificate_id'),
                    })

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or 'https://app.institutoraimongaja.com'
            base_url = base_url.rstrip('/')
            qr_url = "{}/verificar/?{}".format(base_url, urlencode(query_params))

            data = {
                'student_name': self.student_name,
                'diplomado_name': self.diplomado_name,
                'start_date': start_date_str,
                'end_date': end_date_str,
                'duration_hours': self.duration_hours,
                'duration_ects': self.duration_ects,
                'issue_date': issue_date_str,
                'diploma_type': self.diploma_type,
                'subjects_presencial': self.subjects_presencial or '',
                'subjects_online': self.subjects_online or '',
                'qr_url': qr_url,
                'registry_number': self.name,
            }

            pdf_content = self.env['report.irg_generacion_diplomados.diplomado_pdf'].generate_diplomado_pdf(data)

            import base64
            attachment_name = "Diplomado_%s.pdf" % self.student_name.replace(' ', '_')
            attachment = self.env['ir.attachment'].create({
                'name': attachment_name,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'irg.diplomado.registry',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            self.write({'attachment_id': attachment.id})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % self.attachment_id.id,
            'target': 'self',
        }
