from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    last_user_id = fields.Many2one(
        'res.users', 
        string="Comercial Anterior", 
        readonly=True, 
        help="Comercial asignado justo antes del actual."
    )

    def write(self, vals):
        if 'user_id' in vals:
            for lead in self:
                if lead.user_id and lead.user_id.id != vals['user_id']:
                     # Store only if different. Use sudo to avoid permission issues during automation.
                     lead.sudo().write({'last_user_id': lead.user_id.id})
        
        return super(CrmLead, self).write(vals)
