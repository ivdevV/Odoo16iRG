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
            # We want to store the OLD user_id as the previous_user_id
            # before it gets overwritten by the new value in vals.
            
            # Optimization: only update records that actually have a different user_id
            for lead in self:
                if lead.user_id and lead.user_id.id != vals['user_id']:
                     # We write to the specific record to set the previous user.
                     # We use a direct SQL write or separate write to avoid recursion issues usually,
                     # but standard write is fine if we don't trigger infinite recursion.
                     # To be absolutely safe and avoid "dirty inputs" in installation,
                     # we can just write to the field directly on the record object if context allows,
                     # but here we must persist it.
                     
                     # Safe approach: Call super logic for the PREVIOUS field update as a separate transaction step
                     # effectively, but since we are IN a write, we just need to make sure we don't loop.
                     # The previous implementation super(CrmLead, lead).write(...) was technically correct 
                     # but potentially triggered the constraint issue if the record was in a "bad state".
                     
                     # Let's try to update the VALS if possible? 
                     # No, because previous_user_id varies per record.
                     
                     lead.sudo().write({'previous_user_id': lead.user_id.id})
        
        return super(CrmLead, self).write(vals)
