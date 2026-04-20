from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    last_user_id = fields.Many2one(
        'res.users', 
        string="Comercial Anterior", 
        readonly=True, 
        help="Comercial asignado justo antes del actual."
    )

    fecha_reactivacion = fields.Datetime(
        string="Fecha Reactivación",
        help="Fecha en la que el lead fue reactivado (el contacto volvió a pedir información sin necesidad de crear un nuevo lead).",
    )

    # CAMPOS "FANTASMA" PARA EVITAR ERROR DE INSTALACION
    # Definimos estos campos aquí para que Odoo reconozca que existen y NO intente borrar
    # las columnas de la base de datos, lo cual está causando el error de constraint.
    previous_user_id = fields.Many2one('res.users', string="Comercial Anterior (Legacy, ignora esto)")
    x_studio_comercial_actual_irg = fields.Many2one('res.users', string="Comercial Actual (Legacy, ignora esto)")

    def write(self, vals):
        if 'user_id' in vals:
            for lead in self:
                if lead.user_id and lead.user_id.id != vals['user_id']:
                     # Store only if different. Use sudo to avoid permission issues during automation.
                     lead.sudo().write({'last_user_id': lead.user_id.id})
        
        return super(CrmLead, self).write(vals)
