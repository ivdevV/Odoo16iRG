from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    irg_fecha_reactivacion = fields.Datetime(
        string="Fecha de Reactivación",
        help="Fecha en la que el lead fue reactivado.",
    )
    irg_campana_reactivacion = fields.Char(
        string="Campaña de Reactivación",
        help="Nombre de la campaña que originó la reactivación del lead.",
    )
    irg_fuente_reactivacion = fields.Char(
        string="Fuente de Reactivación",
        help="Canal o fuente desde la que se reactivó el lead.",
    )
    irg_referido_reactivacion = fields.Char(
        string="Referido de Reactivación",
        help="Persona o entidad que refirió la reactivación del lead.",
    )
