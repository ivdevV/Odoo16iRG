# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import csv

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

LOCKED_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'done', 'cancel'}
}

class StudentReport(models.Model):
    _name = "student.report.doc"
    _inherit = ['mail.thread', 'mail.activity.mixin']   # <-- add this
    _description = "Student Analysis Report"
    _auto = True
    _order = 'name desc'


    name = fields.Char(
        string="Report Reference",
        required=True, copy=False, readonly=True,
        index='trigram',
        states={'draft': [('readonly', False)]},
        default=lambda self: _('New'))
    date = fields.Date(string = "Fecha de envío", tracking=True) 
    state = fields.Selection(selection=[
                                 ('draft','Borrador'),
                                 ('checked','Revisado'),
                                 ('sent','Enviado'),
                                 ('auth','Autorizado'),
                                 ('cancel','Cancelado')], default='draft', string='Estado', required=True, tracking=True)
    report_lines = fields.One2many(
        comodel_name='student.report.line',
        inverse_name='report_id',
        string="Order Lines",
        states=LOCKED_FIELD_STATES,
        copy=True, auto_join=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)


    csv_file = fields.Binary(
        string="CSV File",
        readonly=True,
        copy=False,
        attachment=True,
        tracking=True,
    )
    csv_filename = fields.Char(
        string="CSV Filename",
        readonly=True,
    )

    ins_count = fields.Integer(string="Inscritos", compute='_compute_admission_status_counts')
    reins_count = fields.Integer(string="Reinscritos", compute='_compute_admission_status_counts')
    baja_count = fields.Integer(string="De Baja", compute='_compute_admission_status_counts')


    data_complete = fields.Boolean(string="Datos completos", compute="_compute_data_complete")


    def _compute_data_complete(self):
        for record in self:
            record.data_complete = all([l.data_complete for l in record.report_lines])  
                                                                       


    @api.depends('report_lines.admission_status')
    def _compute_admission_status_counts(self):
        for record in self:
            lines = record.report_lines
            record.ins_count = len(lines.filtered(lambda r: r.admission_status == 'ins'))
            record.reins_count = len(lines.filtered(lambda r: r.admission_status == 'reins'))
            record.baja_count = len(lines.filtered(lambda r: r.admission_status == 'baja'))


    def action_open_ins_students(self):
        """ Open report lines where admission_status is 'ins' """
        self.ensure_one()
        line_ids = self.report_lines.filtered(lambda r: r.admission_status == 'ins').ids
        return self._open_admissions(line_ids, "Inscritos")

    def action_open_reins_students(self):
        """ Open report lines where admission_status is 'reins' """
        self.ensure_one()
        line_ids = self.report_lines.filtered(lambda r: r.admission_status == 'reins').ids
        return self._open_admissions(line_ids, "Reinscritos")

    def action_open_baja_students(self):
        """ Open report lines where admission_status is 'baja' """
        self.ensure_one()
        line_ids = self.report_lines.filtered(lambda r: r.admission_status == 'baja').ids
        return self._open_admissions(line_ids, "De Baja")


    def _open_admissions(self, line_ids, title):
        """ Open the admission records linked to the report lines """
        admission_ids = []
        for line in self.report_lines:
            if line.id in line_ids and line.admission_id:
                admission_ids.append(line.admission_id.id)

        return {
        'type': 'ir.actions.act_window',
        'name': title,
        'res_model': 'op.admission', 
        'view_mode': 'tree,form',
        'domain': [('id', 'in', admission_ids)],
        'target': 'current',
    }

    # ----------  CSV generation ----------
    def _get_csv_column_order(self):

        line_fields = [
            'admission_status',
            'scholar_year',
            'first_name',
            'middle_name',
            'last_name',
            'gender',
            'curp',
            'date',
            'nationality',
            'lang',
            'special_needs',
            'academic_background',
            'cct',
            'application_number',
            'education_level',
            'institute_key',
            'career_key',
            'shift_type',
            'rvoe_number',
            'rvoe_date',
            'educational_mod',
        ]
        return line_fields

    def action_generate_csv(self):

        # Helper to get display value 
        def get_display_value(line, field_name):
            field_value = line[field_name]
            if not field_value:
                return ''
            field = line._fields[field_name]
            if field.type == 'many2one':
                return field_value.display_name
            elif field.type in ('one2many', 'many2many'):
                return ', '.join(field_value.mapped('display_name'))
            elif field.type == 'selection':
                selection = dict(field._description_selection(line.env))
                return selection.get(field_value, '')
            elif field.type == 'date':
                return field_value.strftime('%d/%m/%Y') if field_value else ''
            elif field.type == 'datetime':
                return field_value.strftime('%d/%m/%Y %H:%M') if field_value else ''
            else:
                return str(field_value)



        self.ensure_one()
        self.report_lines._check_admission()
        if not self.report_lines:
            raise UserError(_("Se requieren registros para reportar."))
        if self.state != 'draft':
            raise UserError(_("CSV solo se puede generar en estado borrador."))

        # Determine the model of the lines
        LineModel = self.report_lines._name
        model_obj = self.env[LineModel]

        line_fields = self._get_csv_column_order()

        # === DYNAMIC HEADER: Get 'string' of each field from model ===
        headers = []
        for field_name in line_fields:
            if field_name not in model_obj._fields:
                headers.append(field_name)  # fallback if field not found
                continue
            field = model_obj._fields[field_name]
            # Get translated string (same as in tree/form views)
            field_string = field.get_description(self.env)["string"]
            headers.append(field_string)

        # Build rows
        rows = [headers]  # First row is dynamic header

        for line in self.report_lines:
            row = [get_display_value(line, f) for f in line_fields]
            rows.append(row)

        # Generate CSV
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)

        # Use UTF-8 with BOM to ensure Excel reads accents correctly (especially on Windows)
        csv_bytes = buffer.getvalue().encode('utf-8-sig')
        b64_data = base64.b64encode(csv_bytes).decode()

        # Save to record
        self.write({
            'csv_file': b64_data,
            'csv_filename': f"{self.name}.csv",
        })

        return True


    # ----------  state change guards ----------
    def _check_csv_before_state_change(self, new_state):
        if new_state != 'draft' and not self.csv_file:
            raise UserError(_("Se requiere el archivo csv generado."))
        if new_state != 'draft' and not self.report_lines:
            raise UserError(_("Se requieren registros para reportar."))

    def action_set_checked(self):
        self._check_csv_before_state_change('checked')
        self.write({'state': 'checked'})
        return 

    def action_set_sent(self):
        self._check_csv_before_state_change('sent')
        self.write({
                   'state': 'sent',
                   'date': fields.Date.today(),
                   })
        return

    def action_set_auth(self):
        self._check_csv_before_state_change('auth')
        self.write({'state': 'auth'})
        return 

    def action_set_cancel(self):
        self.write({'state': 'cancel'})




    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'company_id' in vals:
                self = self.with_company(vals['company_id'])
            if vals.get('name', _("New")) == _("New"):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'student.report', sequence_date=False) or _("New")

        return super().create(vals_list)




class StudentReport(models.Model):
    _name = "student.report.line"
    _description = "Student Analysis Report"
    _auto = True
    _rec_name = 'date'
    _order = 'date desc'

    report_id = fields.Many2one(
        comodel_name='student.report.doc',
        string="Student Report",
        required=True, ondelete='cascade', index=True, copy=False)
    
    company_id = fields.Many2one(
        related='report_id.company_id',
        store=True, index=True, precompute=True)

    admission_id = fields.Many2one('op.admission', string="Aplicación", required=True)
    academic_year = fields.Char(related="admission_id.batch_id.scholar_year", string='Año del ciclo escolar', readonly=True)
    admission_status = fields.Selection([('ins','Inscripción'),('reins','Reinscripción')], related="admission_id.admission_status", string="Estatus", readonly=True)
    first_name = fields.Char(related="admission_id.student_id.first_name", string='Nombre del Alumno', readonly=True,  translate=True)
    middle_name = fields.Char(related="admission_id.student_id.middle_name", string='Primer Apellido', readonly=True, translate=True)
    last_name = fields.Char(related="admission_id.student_id.last_name", string='Segundo Apellido', readonly=True, translate=True)
    curp = fields.Char(related="admission_id.student_id.partner_id.l10n_mx_edi_curp", string='Curp', readonly=True)
    gender = fields.Selection([('m','Masculino'),('','Femenino'),('o','Otro')], related="admission_id.student_id.gender", string='Género', readonly=True)
    date = fields.Date(related="admission_id.student_id.birth_date", string='Fecha de Nacimiento', readonly=True)
    student_id = fields.Many2one( 'op.student', related="admission_id.student_id", string="Estudiante", readonly=True)
    lang = fields.Selection(related="admission_id.student_id.lang", string="Idioma/Lengua")
    nationality = fields.Many2one('res.country', related="admission_id.student_id.nationality", string="Pais de Procedencia", readonly=True)
    partner_id = fields.Many2one('res.partner', related="admission_id.student_id.partner_id",  string="Compañero", readonly=True)
    user_id = fields.Many2one( 'res.users', related="admission_id.student_id.user_id", string="Usuario", readonly=True)
    scholar_year = fields.Char(related="admission_id.batch_id.scholar_year", string="Año Escolar", readonly=True)
    special_needs = fields.Selection([('na','No Aplica'),('disabled','Con discapacidad'),('outstanding','Con aptitudes sobresalientes')], related="admission_id.special_needs" ,string="Necesidades Educativas Especiales", readonly=True)
    academic_background = fields.Selection([('si','Si'),('no','No'),('no_aplica','No Aplica')], related="admission_id.academic_background", string="Presenta Antecedentes Académicos", readonly=True)
    career_key = fields.Char(related="admission_id.course_id.career_key", string="Clave de Carrera", readonly=True)
    rvoe_number = fields.Char(related="admission_id.course_id.rvoe_number", string="Número de RVOE", readonly=True)
    rvoe_date = fields.Date(related="admission_id.course_id.rvoe_date", string="Fecha de RVOE", readonly=True)
    educational_mod = fields.Selection([('escolar','Escolar'),('no_escolar','No Escolarizada'),('mixta','Mixta')], related="admission_id.batch_id.educational_mod", string="Modalidad Educativa", readonly=True)
    shift_type = fields.Selection([('matutino','Matutino'),('vespertino','Vespertino'),('mixto','Mixto')], string="Turno", related="admission_id.batch_id.shift_type")
    education_level = fields.Selection([('profesional','Profesional Asociado'),('tecnico','Técnico Superior Universitario'),('licenciatura','Licenciatura'),('especialidad','Especialidad'),('maestria','Maestria'),('doctorado','Doctorado')], related="admission_id.course_id.education_level" ,string="Nivel Educativo", readonly=True)
    application_number = fields.Char(string='Matricula Institucional', related="admission_id.application_number")
    cct = fields.Selection([('si','Si'),('no','No'),('no_aplica','No Aplica')], string="CCT", related="admission_id.batch_id.cct")
    institute_key = fields.Char(string="Clave de Institución", related="admission_id.course_id.institute_key")
    data_complete = fields.Boolean(string="Datos completos", compute="_compute_data_complete")


    @api.constrains('admission_id')
    def _check_admission(self):
        for record in self:
            registros_duplicados = self.search([
                ('id', '!=', record.id),
                ('admission_id', '=', record.admission_id.id),
                ('report_id.state','not in',['cancel','done']),
            ])
            if registros_duplicados:
                raise ValidationError(f"La admisión '{record.admission_id.display_name}' ya existe en otro reporte activo.")
            if record.admission_id.accepted_percentpie < 100:
                raise ValidationError(f"La admisión '{record.admission_id.display_name}' tiene documentos pendientes.")
            if record.admission_id.pending_payments:
                raise ValidationError(f"La admisión '{record.admission_id.display_name}' tiene pagos pendientes.")

    def _compute_data_complete(self):
        # Obtener todos los campos a validar excluyendo los de la lista campos_sin_validacion
        campos_sin_validacion =['data_complete']
        campos_a_validar = [
            field_name for field_name, field_obj in self._fields.items()
            if field_name not in campos_sin_validacion
        ]

        for record in self:

            completo = True
            for campo in campos_a_validar:
                valor = record[campo]
                # Consideramos vacío: False, None, cadena vacía, lista vacía, etc.
                if valor in (False, None, ''):
                    completo = False
                    break
            record.data_complete = completo                        
                                                                       
                           
                                          
                                     
                                                                                                              
                                              
                                    
                         
                                           
                     

