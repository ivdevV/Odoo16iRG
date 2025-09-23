from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'


    @api.depends('ir_attachment_ids.state','ir_attachment_ids')
    def _compute_accepted_percentage(self):
        res = super()._compute_accepted_percentage()
        for partner in self:
            if partner.accepted_percentage >= 1:
                #Cambiar estatus de la admisión relacionada
                admission_ids = self.env['op.admission'].search([('state','in',['done']),('partner_id','=',partner.id)])
                year = fields.Date.today().year
                generation = self.env['op.academic.year'].search([('name','=',year)])
                academic_term_id =generation.academic_term_ids.filtered(lambda t: t.term_start_date <= fields.Date.today() and t.term_end_date >= fields.Date.today())
                for admission in admission_ids:
                    admission.admission_status = admission.student_report_id.state == 'auth' and 'reins' or 'ins'
                    admission.generation = generation.name
                    admission.period_4month = academic_term_id[0].name
                    admission.academic_term_id = academic_term_id.id
        return res
                
                
