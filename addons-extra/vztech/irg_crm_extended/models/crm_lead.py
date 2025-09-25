from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    current_commercial = fields.Many2one(
        'res.users', string='Current Commercial', store=True)
    
    # current_commercial = fields.Many2one(
    #     'res.users', string='Current Commercial', compute='_compute_current_commercial', store=True)

    # @api.depends('email_from', 'phone', 'user_id')
    # def _compute_current_commercial(self):
    #     for lead in self:
    #         # Asignar el user_id del lead actual por defecto
    #         lead.current_commercial = lead.user_id
    #         normalized_phone = self._normalize_phone(lead.phone)

    #         # Evitar la búsqueda si el registro aún no se ha guardado (no tiene ID)
    #         if not lead.id:
    #             continue

    #         domain = [('id', '!=', lead.id),
    #                   ('create_date', '<', lead.create_date)]

    #         if lead.email_from and normalized_phone:
    #             domain = ['|', ('email_from', '=', lead.email_from),
    #                       ('phone', '=', normalized_phone)] + domain
    #         elif lead.email_from:
    #             domain = [('email_from', '=', lead.email_from)] + domain
    #         elif normalized_phone:
    #             domain = [('phone', '=', normalized_phone)] + domain

    #         # Buscar leads coincidentes anteriores al lead actual
    #         found_leads = self.search(domain, order='create_date ASC', limit=1)

    #         # Asignar el current_commercial al user_id del lead encontrado más antiguo
    #         if found_leads:
    #             lead.current_commercial = found_leads.user_id

    def _normalize_phone(self, phone):
        if phone:
            return ''.join(filter(str.isdigit, phone))
        return None
