# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class OpAdmission(models.Model):
    _inherit = "op.admission"

    state = fields.Selection(selection_add=[('done', 'Vigente')])
    student_report_line_id = fields.Many2one(
        'student.report.line', string="Linea Reporte", ondelete='set null')

    student_report_id = fields.Many2one('student.report.doc', related="student_report_line_id.report_id", string="Folio del Reporte")
    admission_status = fields.Selection(selection_add=[('baja', 'Baja'),('fin','Finalizó')], string="Estatus", ondelete={'baja':'set null', 'fin': 'set null'})

    generation = fields.Char(string="Generación")
    period_4month = fields.Char(string="Cuatrimestre")
    academic_term_id = fields.Many2one('op.academic.term', string="Cuatrimestre_id")
    
    student_report_state = fields.Selection(selection=[
                                 ('draft','Borrador'),
                                 ('checked','Revisado'),
                                 ('sent','Enviado'),
                                 ('auth','Autorizado'),
                                 ('cancel','Cancelado')], related="student_report_id.state", string="Estado del Reporte")

    accepted_percentpie = fields.Float(string ="Documentos Aceptados", compute="_compute_accepted_percentpie")
    pending_payments = fields.Boolean(string ="Pagos Pendientes", compute="_compute_pending_payments")
    course_sepyc_program = fields.Boolean(related="course_id.sepyc_program", store=True)

    def _compute_pending_payments(self):
        for adm in self:
            overdue_payments = adm.order_id.invoice_warning_ids.filtered(lambda inv: inv.invoice_date_due < fields.Date.today() and inv.payment_state in ['not_paid'] and inv.state not in ['draft','cancel'] )
            adm.pending_payments = overdue_payments and True or False

    def _compute_accepted_percentpie(self):
        for adm in self:
            adm.accepted_percentpie = adm.accepted_percentage * 100

    def action_generate_student_report(self):
        """Create a new student.report.doc with the qualifying admissions
        and return an action that opens it in form view."""
        # filter the valid admissions
        valid_admissions = self.filtered(
            lambda rec: (
                rec.accepted_percentpie >= 100 and
                (not rec.student_report_line_id or
                 rec.student_report_line_id.report_id.state in ['done', 'cancel']) and
               not rec.pending_payments
            )
        )

        if not valid_admissions:
            return  # nothing to do, or raise UserError if preferred

        # build the line values
        line_vals = [
            (0, 0, {'admission_id': adm.id})
            for adm in valid_admissions
        ]

        # create the report
        report = self.env['student.report.doc'].create({
            'report_lines': line_vals,
        })
        for line in report.report_lines: # Link admission to new report
            line.admission_id.student_report_line_id = line.id

        # open the newly created record
        return {
            'type': 'ir.actions.act_window',
            'name': _('Student Analysis Report'),
            'res_model': 'student.report.doc',
            'view_mode': 'form',
            'res_id': report.id,
            'target': 'current',
        }

    def cron_update_admission_status(self):
        admission_ids = self.search([('state','=','done'),('admission_status','=','ins')])
        year = fields.Date.today().year
        generation = self.env['op.academic.year'].search([('name','=',year)])
        academic_term_id =generation.academic_term_ids.filtered(lambda t: t.term_start_date <= fields.Date.today() and t.term_end_date >= fields.Date.today())[0]
        
        for admission in admission_ids:
            if admission.academic_term_id and admission.academic_term_id.term_end_date < academic_term_id.term_start_date:
                admission.admission_status = 'reins'
                admission.generation = generation.name
                admission.academic_term_id = academic_term_id.id
                admission.period_4month = academic_term_id[0].name
                        
        
        
       




