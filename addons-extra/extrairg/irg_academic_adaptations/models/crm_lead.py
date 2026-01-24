
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
    x_studio_char_field_iRhji = fields.Char("Comercial actual")
    
    # CAMPOS LEGACY (NO BORRAR para evitar error de upgrade crm_lead_message_main_attachment_id_fkey)
    # Estos campos fueron creados por error en commit 0112c3a0 y la BD los tiene.
    # Los mantenemos aquí para que Odoo no intente borrarlos y falle.
    x_studio_comercial_actual_irg = fields.Many2one('res.users', "Comercial Actual (Legacy)")
    previous_user_id = fields.Many2one('res.users', string="Comercial Anterior (Legacy)", readonly=True)
