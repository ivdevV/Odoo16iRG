from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    previous_user_id = fields.Many2one(
        'res.users', 
        string="Comercial Anterior", 
        readonly=True, 
        help="Comercial asignado justo antes del actual."
    )

    def write(self, vals):
        if 'user_id' in vals:
            for lead in self:
                # Capture current user as previous before the write occurs
                if lead.user_id:
                     super(CrmLead, lead).write({'previous_user_id': lead.user_id.id})
        
        return super(CrmLead, self).write(vals)
