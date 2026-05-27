# -*- coding: utf-8 -*-
import logging
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Redefinimos stripe_subscription_id como Many2one apuntando a stripe.subscription
    stripe_subscription_id = fields.Many2one(
        'stripe.subscription',
        string='Suscripción Stripe (Model)',
        copy=False,
        ondelete='restrict',
        tracking=True
    )
    
    stripe_payment_link_id = fields.Many2one(
        'stripe.payment.link',
        string='Enlace de Pago Stripe',
        copy=False,
        ondelete='restrict',
        tracking=True
    )

    stripe_payment_link_url = fields.Char(
        related='stripe_payment_link_id.url',
        string='URL Enlace de Pago',
        readonly=True
    )

    stripe_customer_id = fields.Char(
        related='partner_id.stripe_customer_id',
        string='ID Cliente Stripe',
        readonly=True
    )

    # ------------------------------------------------------------------
    # Interceptamos Escritura/Creación para mapear String a Many2one ID
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'stripe_subscription_id' in vals and isinstance(vals['stripe_subscription_id'], str):
                stripe_id = vals['stripe_subscription_id']
                if stripe_id:
                    partner_id = vals.get('partner_id')
                    sub_record = self.env['stripe.subscription'].sudo()._find_or_create_from_stripe_id(
                        stripe_id, partner_id=partner_id
                    )
                    vals['stripe_subscription_id'] = sub_record.id
                else:
                    vals['stripe_subscription_id'] = False
        return super(SaleOrder, self).create(vals_list)

    def write(self, vals):
        if 'stripe_subscription_id' in vals and isinstance(vals['stripe_subscription_id'], str):
            stripe_id = vals['stripe_subscription_id']
            if stripe_id:
                partner_id = vals.get('partner_id') or self.partner_id.id
                sub_record = self.env['stripe.subscription'].sudo()._find_or_create_from_stripe_id(
                    stripe_id, partner_id=partner_id
                )
                vals['stripe_subscription_id'] = sub_record.id
            else:
                vals['stripe_subscription_id'] = False
        return super(SaleOrder, self).write(vals)

    # ------------------------------------------------------------------
    # Sobreescritura de Métodos de Stripe Subscription Bridge para compatibilidad
    # ------------------------------------------------------------------

    def _irg_create_stripe_subscription(self):
        """Heredamos para sincronizar inmediatamente la suscripción creada en Stripe."""
        sub_id = super(SaleOrder, self)._irg_create_stripe_subscription()
        if sub_id:
            # Aseguramos la existencia y sincronización del objeto local
            sub_rec = self.env['stripe.subscription'].sudo()._find_or_create_from_stripe_id(
                sub_id, partner_id=self.partner_id.id
            )
            # Refrescamos desde la API de Stripe si es posible
            provider = self._irg_get_stripe_provider()
            if provider:
                try:
                    response = provider._stripe_make_request(f"subscriptions/{sub_id}", method='GET')
                    if response and not response.get('error'):
                        self.env['stripe.sync'].sudo()._sync_subscription_object(response)
                except Exception:
                    _logger.warning("No se pudo refrescar la suscripción recién creada %s en Stripe", sub_id)
        return sub_id

    def _irg_cancel_stripe_subscription(self, invoice_now=False):
        """Sobreescribimos para extraer el ID string desde el Many2one."""
        self.ensure_one()
        sub_id = self.stripe_subscription_id.stripe_id if self.stripe_subscription_id else False
        if not sub_id:
            return True

        provider = self._irg_get_stripe_provider()
        if not provider:
            return False

        payload = {}
        if invoice_now:
            payload["invoice_now"] = "true"
            payload["prorate"] = "true"

        try:
            response = provider._stripe_make_request(f"subscriptions/{sub_id}", payload=payload, method="DELETE")
            if response and not response.get('error'):
                self.env['stripe.sync'].sudo()._sync_subscription_object(response)
        except Exception:
            _logger.exception("Error cancelando suscripción %s en Stripe", sub_id)
            return False
        return True

    def _irg_pause_stripe_subscription(self):
        """Sobreescribimos para extraer el ID string desde el Many2one."""
        self.ensure_one()
        sub_id = self.stripe_subscription_id.stripe_id if self.stripe_subscription_id else False
        if not sub_id:
            return True

        provider = self._irg_get_stripe_provider()
        if not provider:
            return False

        try:
            response = provider._stripe_make_request(
                f"subscriptions/{sub_id}",
                payload={"pause_collection[behavior]": "void"},
            )
            if response and not response.get('error'):
                self.env['stripe.sync'].sudo()._sync_subscription_object(response)
        except Exception:
            _logger.exception("Error pausando suscripción %s en Stripe", sub_id)
            return False
        return True

    def _irg_resume_stripe_subscription(self):
        """Sobreescribimos para extraer el ID string desde el Many2one."""
        self.ensure_one()
        sub_id = self.stripe_subscription_id.stripe_id if self.stripe_subscription_id else False
        if not sub_id:
            return True

        provider = self._irg_get_stripe_provider()
        if not provider:
            return False

        try:
            response = provider._stripe_make_request(
                f"subscriptions/{sub_id}",
                payload={"pause_collection": ""},
            )
            if response and not response.get('error'):
                self.env['stripe.sync'].sudo()._sync_subscription_object(response)
        except Exception:
            _logger.exception("Error reanudando suscripción %s en Stripe", sub_id)
            return False
        return True

    def action_irg_create_stripe_subscription(self):
        """Sobreescribimos la acción manual para compatibilidad con el Many2one."""
        self.ensure_one()
        if self.stripe_subscription_id:
            raise UserError(
                _("Esta suscripción ya tiene un ID de Stripe: %s")
                % self.stripe_subscription_id.stripe_id
            )
        if not self.is_subscription:
            raise UserError(_("Este pedido no es una suscripción."))

        stripe_mode = getattr(self, 'irg_subscription_stripe_mode', False)
        if stripe_mode != 'payment_link_fallback' and not self.payment_token_id:
            raise UserError(
                _("No hay token de pago asignado. El cliente debe completar "
                  "un primer pago con tarjeta antes de crear la suscripción en Stripe.")
            )

        sub_id = self._irg_create_stripe_subscription()
        if not sub_id:
            raise UserError(
                _("No se pudo crear la suscripción en Stripe. "
                  "Revise los logs para más detalles.")
            )

        self.message_post(
            body=(
                "✅ <b>Suscripción Stripe creada manualmente.</b><br/>"
                "ID: <code>%s</code>" % sub_id
            ),
            message_type="notification",
            subtype_xmlid="mail.mt_note",
        )
        return True

    # ------------------------------------------------------------------
    # Botones Interactivos en el Presupuesto
    # ------------------------------------------------------------------

    def action_irg_create_stripe_customer(self):
        """Crea el cliente en Stripe si no tiene stripe_customer_id aún."""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("No hay cliente asignado a este presupuesto."))
        
        customer_id = self.partner_id._irg_ensure_stripe_customer()
        if not customer_id:
            raise UserError(_("No se pudo crear/vincular el cliente en Stripe."))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Cliente Vinculado"),
                'message': _("Se ha creado/vinculado el cliente en Stripe: %s") % customer_id,
                'sticky': False,
            }
        }

    def action_irg_create_stripe_payment_link(self):
        """Crea un Payment Link en Stripe asociado al precio de la suscripción."""
        self.ensure_one()
        provider = self._irg_get_stripe_provider()
        if not provider:
            raise UserError(_("No se ha encontrado un proveedor de Stripe activo."))

        # 1. Asegurar el precio en Stripe
        price_id = self._irg_ensure_stripe_price(provider=provider)
        if not price_id:
            raise UserError(_("No se pudo generar el precio en Stripe para este pedido."))

        term_number = self.term_number or 1
        cuota = round(self.amount_total / term_number, 2)
        currency_name = self.currency_id.name or "EUR"
        description = "%s - %s cuotas de %s %s (Total: %s %s)" % (
            self.name or "",
            term_number,
            cuota,
            currency_name,
            self.amount_total,
            currency_name
        )
        if len(description) > 500:
            description = description[:497] + "..."

        # 2. Crear el Payment Link en Stripe
        payload = {
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": "1",
            "metadata[odoo_order_id]": str(self.id),
            "metadata[odoo_order_name]": self.name or "",
        }

        if self.is_subscription:
            payload.update({
                "subscription_data[metadata][odoo_order_id]": str(self.id),
                "subscription_data[metadata][odoo_order_name]": self.name or "",
                "subscription_data[description]": description,
            })


        try:
            response = provider._stripe_make_request("payment_links", payload=payload)
            if response and not response.get('error'):
                plink_id = response.get('id')
                url = response.get('url')
                if url:
                    url = f"{url}?client_reference_id=odoo_order_{self.id}"
                active = response.get('active', True)
                
                # Registramos localmente el Payment Link
                vals = {
                    'name': f"Enlace de pago - {self.name}",
                    'stripe_id': plink_id,
                    'url': url,
                    'active': active,
                    'is_recurring': self.is_subscription,
                    'price_id': price_id,
                    'metadata_json': json.dumps(response.get('metadata', {})),
                }
                link_rec = self.env['stripe.payment.link'].sudo()._find_or_create_from_stripe_id(plink_id, vals)
                
                # Vinculamos a la orden y al cliente
                self.sudo().write({'stripe_payment_link_id': link_rec.id})
                if self.partner_id:
                    self.partner_id.sudo().write({
                        'stripe_payment_link_ids': [(4, link_rec.id)]
                    })
                
                self.message_post(
                    body=_(
                        "🔗 <b>Enlace de pago de Stripe generado exitosamente.</b><br/>"
                        "URL: <a href='%s' target='_blank'>%s</a>"
                    ) % (url, url),
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Enlace Creado"),
                        'message': _("El enlace de pago se ha creado y asociado correctamente."),
                        'sticky': False,
                    }
                }
            else:
                error_msg = response.get('error', {}).get('message', 'Error desconocido')
                raise UserError(_("Error al crear Payment Link en Stripe: %s") % error_msg)
        except Exception as e:
            _logger.exception("Error al crear Payment Link para pedido %s", self.name)
            raise UserError(_("Error de comunicación con Stripe: %s") % str(e))
