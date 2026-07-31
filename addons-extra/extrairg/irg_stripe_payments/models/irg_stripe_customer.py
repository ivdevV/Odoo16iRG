# -*- coding: utf-8 -*-
"""Customers de Stripe asociados a un contacto.

Existe porque la relación real es **N a 1**, no 1 a 1: una misma persona genera
varios ``cus_...`` distintos con toda normalidad —paga con dos tarjetas, entra por
dos checkouts, o el propio Stripe crea uno nuevo en un Payment Link—. El campo
``res_partner.irg_stripe_customer_id`` que traía ``irg_payment_stripe_recurring``
es un ``Char``: solo cabe uno, así que el segundo Customer de una persona no tenía
dónde guardarse y acababa en la cola de revisión como si fuera un conflicto.

Caso real medido en beta: un contacto con **cinco** Customers de Stripe, de los que
solo uno estaba registrado. Los pagos de los otros cuatro no se vinculaban solos.

El ``Char`` antiguo se conserva y se mantiene sincronizado con el Customer marcado
como principal, para no romper a ``irg_payment_stripe_recurring``, que lo lee.
"""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class IrgStripeCustomer(models.Model):
    _name = 'irg.stripe.customer'
    _description = 'Customer de Stripe vinculado a un contacto'
    _rec_name = 'stripe_id'
    _order = 'partner_id, is_primary desc, id'

    stripe_id = fields.Char(
        string='Customer Stripe', required=True, index=True,
        help="Identificador `cus_...` tal cual viene de Stripe.")
    partner_id = fields.Many2one(
        'res.partner', string='Contacto', required=True, index=True, ondelete='cascade')
    is_primary = fields.Boolean(
        string='Principal',
        help="El que se refleja en el campo antiguo `irg_stripe_customer_id` del "
             "contacto, que siguen leyendo otros módulos.")
    source = fields.Selection(
        [
            ('manual', 'Vinculado a mano'),
            ('metadata', 'metadata.odoo_partner_id'),
            ('auto', 'Resolución automática'),
            ('legacy', 'Campo antiguo del contacto'),
        ],
        string='Origen', default='auto', required=True,
        help="Cómo se estableció el vínculo. Sirve para auditar de qué te puedes fiar.")
    note = fields.Text(string='Nota')

    _sql_constraints = [
        ('stripe_id_uniq', 'unique(stripe_id)',
         "Ese Customer de Stripe ya está vinculado a un contacto. Un Customer "
         "pertenece a una sola persona; una persona puede tener varios Customers."),
    ]

    @api.constrains('stripe_id')
    def _check_stripe_id(self):
        for record in self:
            if not (record.stripe_id or '').strip():
                raise ValidationError(_("El Customer de Stripe no puede estar vacío."))

    # ------------------------------------------------------------------
    @api.model
    def _irg_register(self, partner, stripe_id, source='auto', note=False):
        """Asocia ``stripe_id`` a ``partner``. Idempotente.

        Devuelve ``(registro, conflicto)``. ``conflicto`` es el contacto que ya tenía
        ese Customer cuando es **otro** distinto: eso sí es una incidencia real y la
        decide una persona, no este método. Que un contacto acumule varios Customers
        dejó de serlo.
        """
        if not partner or not stripe_id:
            return self.browse(), None

        stripe_id = stripe_id.strip()
        existing = self.sudo().search([('stripe_id', '=', stripe_id)], limit=1)
        if existing:
            if existing.partner_id == partner:
                return existing, None
            return existing, existing.partner_id

        record = self.sudo().create({
            'stripe_id': stripe_id,
            'partner_id': partner.id,
            'source': source,
            'note': note or False,
            # El primero que se registre manda sobre el campo antiguo.
            'is_primary': not partner.sudo().irg_stripe_customer_id,
        })
        record._irg_sync_legacy_field()
        return record, None

    def _irg_sync_legacy_field(self):
        """Refleja el Customer principal en el ``Char`` que leen otros módulos."""
        for record in self:
            if not record.is_primary:
                continue
            partner = record.partner_id.sudo()
            if partner.irg_stripe_customer_id != record.stripe_id:
                partner.write({'irg_stripe_customer_id': record.stripe_id})

    def action_make_primary(self):
        self.ensure_one()
        siblings = self.sudo().search([
            ('partner_id', '=', self.partner_id.id), ('id', '!=', self.id)])
        siblings.write({'is_primary': False})
        self.sudo().write({'is_primary': True})
        self._irg_sync_legacy_field()
        return True

    @api.model
    def _irg_partner_for(self, stripe_id):
        """Contacto dueño de ese Customer, o recordset vacío."""
        if not stripe_id:
            return self.env['res.partner'].browse()
        record = self.sudo().search([('stripe_id', '=', stripe_id.strip())], limit=1)
        return record.partner_id
