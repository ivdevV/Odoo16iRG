# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StripeSubscription(models.Model):
    _name = 'stripe.subscription'
    _description = 'Stripe Subscription'
    _order = 'current_period_end desc, id desc'

    name = fields.Char(string='Nombre', required=True)
    stripe_id = fields.Char(string='ID Suscripción Stripe', required=True, index=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', ondelete='restrict')
    status = fields.Selection([
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('paused', 'Paused')
    ], string='Estado Stripe', index=True, default='incomplete')
    
    current_period_start = fields.Datetime(string='Inicio Período Actual')
    current_period_end = fields.Datetime(string='Fin Período Actual')
    cancel_at_period_end = fields.Boolean(string='Cancelar al fin del ciclo', default=False)
    
    price_id = fields.Char(string='ID Precio Stripe')
    product_id = fields.Char(string='ID Producto Stripe')
    
    amount = fields.Monetary(string='Importe Recurrente', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Moneda')
    
    interval = fields.Selection([
        ('day', 'Día'),
        ('week', 'Semana'),
        ('month', 'Mes'),
        ('year', 'Año')
    ], string='Intervalo')
    
    latest_invoice_id = fields.Char(string='Última Factura Stripe')
    metadata_json = fields.Text(string='Metadatos JSON')
    raw_payload = fields.Text(string='Payload Bruto Stripe')

    _sql_constraints = [
        ('stripe_id_unique', 'unique(stripe_id)', 'El ID de suscripción de Stripe debe ser único.'),
    ]

    @api.model
    def _find_or_create_from_stripe_id(self, stripe_id, partner_id=False):
        """Helper para buscar o crear un registro local basado en el ID de Stripe."""
        if not stripe_id:
            return self.env['stripe.subscription']
        
        subscription = self.search([('stripe_id', '=', stripe_id)], limit=1)
        if not subscription:
            name = f"Sub. Stripe {stripe_id}"
            vals = {
                'name': name,
                'stripe_id': stripe_id,
            }
            if partner_id:
                vals['partner_id'] = partner_id
            subscription = self.create(vals)
        return subscription

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
            response = provider._stripe_make_request(f"subscriptions/{self.stripe_id}", method='GET')
            if response and not response.get('error'):
                self.env['stripe.sync'].sudo()._sync_subscription_object(response)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Sincronización Exitosa"),
                        'message': _("La suscripción se ha actualizado desde Stripe."),
                        'sticky': False,
                    }
                }
            else:
                error_msg = response.get('error', {}).get('message', 'Error desconocido')
                raise UserError(_("Error al consultar Stripe: %s") % error_msg)
        except Exception as e:
            _logger.exception("Error consultando suscripción %s en Stripe", self.stripe_id)
            raise UserError(_("Error de conexión con Stripe: %s") % str(e))

    def action_cancel_stripe(self):
        """Cancela la suscripción en Stripe y actualiza el estado local."""
        self.ensure_one()
        provider = self.env['payment.provider'].sudo().search([
            ('code', '=', 'stripe'),
            ('state', 'in', ('enabled', 'test'))
        ], limit=1)
        if not provider:
            raise UserError(_("No se ha encontrado un proveedor de Stripe activo."))

        try:
            response = provider._stripe_make_request(f"subscriptions/{self.stripe_id}", method='DELETE')
            if response and not response.get('error'):
                self.env['stripe.sync'].sudo()._sync_subscription_object(response)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Suscripción Cancelada"),
                        'message': _("La suscripción ha sido cancelada en Stripe."),
                        'sticky': False,
                    }
                }
            else:
                error_msg = response.get('error', {}).get('message', 'Error desconocido')
                raise UserError(_("Error al cancelar en Stripe: %s") % error_msg)
        except Exception as e:
            _logger.exception("Error cancelando suscripción %s en Stripe", self.stripe_id)
            raise UserError(_("Error de conexión con Stripe: %s") % str(e))
