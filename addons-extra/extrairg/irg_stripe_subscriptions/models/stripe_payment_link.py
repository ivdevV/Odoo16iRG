# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StripePaymentLink(models.Model):
    _name = 'stripe.payment.link'
    _description = 'Stripe Payment Link'

    name = fields.Char(string='Nombre', required=True)
    stripe_id = fields.Char(string='ID Payment Link Stripe', required=True, index=True)
    url = fields.Char(string='URL de Pago', required=True)
    active = fields.Boolean(string='Activo', default=True)
    is_recurring = fields.Boolean(string='Genera Suscripción', default=False)
    price_id = fields.Char(string='ID Precio Stripe')
    partner_ids = fields.Many2many('res.partner', string='Clientes Vinculados')
    metadata_json = fields.Text(string='Metadatos JSON')

    _sql_constraints = [
        ('stripe_id_unique', 'unique(stripe_id)', 'El ID del enlace de pago de Stripe debe ser único.'),
    ]

    @api.model
    def _find_or_create_from_stripe_id(self, stripe_id, vals=None):
        """Helper para buscar o crear un registro local basado en el ID de Stripe."""
        if not stripe_id:
            return self.env['stripe.payment.link']
        
        link = self.search([('stripe_id', '=', stripe_id)], limit=1)
        if not link:
            if not vals:
                vals = {
                    'name': f"Payment Link {stripe_id}",
                    'stripe_id': stripe_id,
                    'url': f"https://buy.stripe.com/{stripe_id}",
                }
            link = self.create(vals)
        elif vals:
            link.write(vals)
        return link

    def action_refresh_from_stripe(self):
        """Consulta la API de Stripe para actualizar este registro local."""
        self.ensure_one()
        provider = self.env['payment.provider'].sudo().search([
            ('code', '=', 'stripe'),
            ('state', 'in', ('enabled', 'test'))
        ], limit=1)
        if not provider:
            raise UserError(_("No se ha encontrado un proveedor de Stripe activo."))

        try:
            response = provider._stripe_make_request(f"payment_links/{self.stripe_id}", method='GET')
            if response and not response.get('error'):
                self.env['stripe.sync'].sudo()._sync_payment_link_object(response)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Sincronización Exitosa"),
                        'message': _("El enlace de pago se ha actualizado desde Stripe."),
                        'sticky': False,
                    }
                }
            else:
                error_msg = response.get('error', {}).get('message', 'Error desconocido')
                raise UserError(_("Error al consultar Stripe: %s") % error_msg)
        except Exception as e:
            _logger.exception("Error consultando payment link %s en Stripe", self.stripe_id)
            raise UserError(_("Error de conexión con Stripe: %s") % str(e))
