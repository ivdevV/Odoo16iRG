from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    irg_event_id = fields.Char(
        string="ID de evento",
        help="Identificador del evento de marketing asociado al lead.",
    )
    fbc = fields.Char(
        string="FBC",
        help="Identificador de cookie de clic de Facebook asociado al lead.",
    )
    fbp = fields.Char(
        string="FBP",
        help="Identificador de navegador de Facebook asociado al lead.",
    )
    event_id_reactivacion = fields.Char(
        string="ID de evento de reactivación",
        help="Identificador del evento de marketing asociado a la reactivación.",
    )
    fbclid_reactivacion = fields.Char(
        string="FBCLID de reactivación",
        help="Identificador de clic de Facebook asociado a la reactivación.",
    )
    fbc_reactivacion = fields.Char(
        string="FBC de reactivación",
        help="Identificador de cookie de clic de Facebook asociado a la reactivación.",
    )
    fbp_reactivacion = fields.Char(
        string="FBP de reactivación",
        help="Identificador de navegador de Facebook asociado a la reactivación.",
    )
    irg_ad_reactivacion = fields.Char(
        string="Anuncio de reactivación",
        help="Identificador o nombre del anuncio asociado a la reactivación.",
    )
