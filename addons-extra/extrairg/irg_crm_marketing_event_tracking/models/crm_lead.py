from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    event_id = fields.Char(
        string="ID de evento",
        help="Identificador del evento de marketing asociado al lead.",
    )
    event_id_reactivacion = fields.Char(
        string="ID de evento de reactivación",
        help="Identificador del evento de marketing asociado a la reactivación.",
    )
    irg_ad_reactivacion = fields.Char(
        string="Anuncio de reactivación",
        help="Identificador o nombre del anuncio asociado a la reactivación.",
    )
