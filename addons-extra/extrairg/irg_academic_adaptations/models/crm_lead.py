
import logging
# from mailchimp3 import MailChimp
from odoo import api, fields, models, _
from odoo.models import expression
from odoo.exceptions import UserError, ValidationError
import multiprocessing as mp

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'
    x_studio_delegacion = fields.Char("Delegación")
    x_studio_modalidad = fields.Char("Modalidad")
    x_studio_formacion = fields.Text("Formación")
    x_studio_referencia_interna_del_producto = fields.Char("Referencia interna del producto")
    x_studio_cdigo_de_modalidad = fields.Char("Código de Modalidad")
    x_studio_cdigo_de_delegacin = fields.Char("Código de Delegación")
    x_studio_ga = fields.Char("ga")
    x_studio_id_curso = fields.Char("ID Curso")
    x_studio_nombre_del_programa = fields.Char("Nombre del programa")
    x_studio_ltimos_estudios = fields.Char("Últimos estudios")
    x_studio_medio = fields.Char("Medio")
    x_studio_campaa = fields.Char("Campaña")
    x_studio_fuente = fields.Char("Fuente")
    x_studio_id_curso_1 = fields.Char("ID Curso")
    x_studio_grupo_de_anuncio = fields.Char("Grupo de anuncio")
    x_studio_keyword = fields.Char("Keyword")
    x_studio_quiere_contacto_por_whatsapp = fields.Char("Quiere contacto por WhatsApp")
    x_studio_tipo_de_lead_1 = fields.Selection([('Encuesta','Encuesta'),('Referido','Referido'),('Antiguo Alumno','Antiguo Alumno'),('Entrada normal','Entrada normal'),('Cita Calendly','Cita Calendly'),('Webinar','Webinar'),('Whatsapp','Whatsapp'),('Portal','Portal')],string='Tipo de lead',)
    x_studio_comercial_actual_irg = fields.Many2one('res.users', "Comercial Actual")
    previous_user_id = fields.Many2one('res.users', string="Comercial Anterior", readonly=True, help="Comercial asignado justo antes del actual.")

    def write(self, vals):
        if 'user_id' in vals:
            # For each record being updated, save the current user_id as previous_user_id
            # However, write is a mass operation, but logic might vary if records have different current users.
            # Best practice for accuracy is to iterate, but for performance in mass write strictness might vary.
            # Odoo's write handles vals for all IDs.
            # To set previous_user_id cleanly for EACH record based on its own current user_id:
            for lead in self:
                if lead.user_id:
                     super(CrmLead, lead).write({'previous_user_id': lead.user_id.id})
        
        return super(CrmLead, self).write(vals)
