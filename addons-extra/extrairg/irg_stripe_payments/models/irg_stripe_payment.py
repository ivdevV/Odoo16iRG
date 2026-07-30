# -*- coding: utf-8 -*-
"""Ledger local de pagos de Stripe.

INVARIANTE: este modelo es de SOLO LECTURA respecto al dinero de Odoo. Observa y
enlaza; nunca concilia. No escribe ``sale.note.inv.legacy``, no toca
``sale.subscription.schedule``, no crea ``account.move`` ni ``account.payment`` y no
muta campos de dinero de ``sale.order``. Esa conciliación es exclusiva de
``stripe.sync._sync_invoice_paid`` / ``_register_paid_invoice_on_schedule`` en
``irg_stripe_subscriptions``.

Es esta invariante la que hace estructuralmente imposible el doble conteo cuando un
mismo pago llega por varios eventos (``payment_intent.succeeded``,
``checkout.session.completed``, ``invoice.paid``) o por el backfill.
"""
import json
import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrgStripePayment(models.Model):
    _name = 'irg.stripe.payment'
    _description = 'Pago Stripe'
    _order = 'payment_date desc, id desc'
    _rec_name = 'stripe_id'

    # Confianza relativa de cada método de match. El upsert nunca degrada un match
    # ya establecido a otro de menor confianza (p. ej. un webhook posterior sin
    # metadata no debe pisar un match hecho por payment.transaction).
    MATCH_CONFIDENCE = {
        'manual': 110,
        'payment_transaction': 100,
        'client_reference_id': 90,
        'object_metadata': 80,
        'customer_metadata': 70,
        'stripe_customer_id': 60,
        'student_email_unique': 40,
        'email_unique': 30,
    }

    # Campos que el upsert nunca sobrescribe con un valor vacío.
    _PROTECTED_FROM_BLANKING = (
        'partner_id', 'sale_order_id', 'move_id', 'payment_transaction_id',
        'stripe_subscription_id', 'stripe_invoice_id', 'stripe_checkout_session_id',
        'stripe_charge_id', 'stripe_payment_intent_id', 'stripe_customer_id',
        'stripe_customer_email', 'receipt_url', 'hosted_invoice_url', 'description',
    )

    # --- Identificadores Stripe -------------------------------------------------
    stripe_id = fields.Char(
        string='ID Stripe',
        required=True,
        index=True,
        copy=False,
        help="Ancla de idempotencia: el PaymentIntent (pi_...) si existe, si no el Charge (ch_...).",
    )
    stripe_payment_intent_id = fields.Char(string='PaymentIntent', index=True, copy=False)
    stripe_charge_id = fields.Char(string='Charge', index=True, copy=False)
    stripe_checkout_session_id = fields.Char(string='Checkout Session', index=True, copy=False)
    stripe_invoice_id = fields.Char(string='Factura Stripe', index=True, copy=False)
    stripe_customer_id = fields.Char(string='Customer Stripe', index=True, copy=False)
    stripe_customer_email = fields.Char(string='Email en Stripe')

    # --- Identidad --------------------------------------------------------------
    partner_id = fields.Many2one(
        'res.partner',
        string='Contacto',
        index=True,
        ondelete='restrict',
    )
    partner_state = fields.Selection(
        [
            ('linked', 'Vinculado'),
            ('review', 'Pendiente de revisión'),
            ('unlinked', 'Sin vincular'),
        ],
        string='Estado de vinculación',
        default='unlinked',
        required=True,
        index=True,
    )
    partner_match_method = fields.Selection(
        [
            ('payment_transaction', 'Transacción de pago Odoo'),
            ('client_reference_id', 'client_reference_id'),
            ('object_metadata', 'Metadata del objeto'),
            ('customer_metadata', 'Metadata del Customer'),
            ('stripe_customer_id', 'Customer ID guardado'),
            ('student_email_unique', 'Email único de alumno'),
            ('email_unique', 'Email único de contacto'),
            ('manual', 'Manual'),
        ],
        string='Método de vinculación',
        help="Cómo se decidió el contacto. Sirve de rastro de auditoría: los métodos "
             "basados en email son los menos fiables.",
    )
    review_id = fields.Many2one(
        'irg.stripe.identity.review',
        string='Revisión de identidad',
        ondelete='set null',
        index=True,
    )
    student_id = fields.Many2one(
        'op.student',
        string='Alumno',
        compute='_compute_student_id',
        search='_search_student_id',
    )

    # --- Dinero -----------------------------------------------------------------
    state = fields.Selection(
        [
            ('succeeded', 'Pagado'),
            ('failed', 'Fallido'),
            ('canceled', 'Cancelado'),
            ('refunded', 'Reembolsado'),
            ('partially_refunded', 'Reembolsado parcialmente'),
        ],
        string='Estado',
        default='succeeded',
        required=True,
        index=True,
    )
    amount = fields.Monetary(string='Importe', currency_field='currency_id')
    amount_refunded = fields.Monetary(string='Reembolsado', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Moneda')
    stripe_currency = fields.Char(
        string='Divisa Stripe',
        help="Código de divisa tal cual lo devuelve Stripe. Se conserva siempre, incluso "
             "si esa divisa no existe en Odoo y por tanto currency_id queda vacío.",
    )
    payment_date = fields.Datetime(string='Fecha de pago', index=True)

    # --- Contexto ---------------------------------------------------------------
    description = fields.Char(string='Descripción')
    receipt_url = fields.Char(string='Recibo Stripe')
    hosted_invoice_url = fields.Char(string='Factura Stripe (URL)')
    sale_order_id = fields.Many2one('sale.order', string='Pedido', ondelete='set null', index=True)
    move_id = fields.Many2one('account.move', string='Factura Odoo', ondelete='set null', index=True)
    payment_transaction_id = fields.Many2one(
        'payment.transaction', string='Transacción Odoo', ondelete='set null', index=True)
    stripe_subscription_id = fields.Many2one(
        'stripe.subscription', string='Suscripción Stripe', ondelete='set null', index=True)
    is_subscription_payment = fields.Boolean(
        string='Pago de suscripción',
        compute='_compute_is_subscription_payment',
        store=True,
        help="Verdadero si el pago lleva factura de Stripe asociada, es decir, procede del "
             "ciclo de facturación de una suscripción y no de un cobro suelto.",
    )
    origin = fields.Selection(
        [
            ('webhook', 'Webhook'),
            ('backfill', 'Backfill'),
            ('manual', 'Manual'),
        ],
        string='Origen',
        default='webhook',
        required=True,
        index=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Compañía', default=lambda self: self.env.company)
    raw_payload = fields.Text(string='Payload Bruto Stripe')

    _sql_constraints = [
        ('stripe_id_unique', 'unique(stripe_id)', 'El ID de Stripe debe ser único.'),
    ]

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('stripe_invoice_id')
    def _compute_is_subscription_payment(self):
        for payment in self:
            payment.is_subscription_payment = bool(payment.stripe_invoice_id)

    @api.depends('partner_id')
    def _compute_student_id(self):
        student_obj = self.env['op.student'].sudo()
        for payment in self:
            student = student_obj.search(
                [('partner_id', '=', payment.partner_id.id)], limit=1
            ) if payment.partner_id else student_obj
            payment.student_id = student.id if student else False

    def _search_student_id(self, operator, value):
        students = self.env['op.student'].sudo().search([('id', operator, value)])
        return [('partner_id', 'in', students.mapped('partner_id').ids)]

    def name_get(self):
        result = []
        for payment in self:
            label = payment.stripe_id or ''
            if payment.partner_id:
                label = f"{label} · {payment.partner_id.name}"
            result.append((payment.id, label))
        return result

    # ------------------------------------------------------------------
    # Extractores agnósticos de forma
    #
    # La versión de API de los payloads de *webhook* la fija el endpoint en el
    # Dashboard de Stripe y puede diferir de la de las llamadas API. El mismo
    # PaymentIntent puede llegar con `charges.data[0]` por webhook y con
    # `latest_charge` por API. Estos helpers miran todas las formas conocidas, en
    # el mismo estilo defensivo que `_extract_subscription_id_from_invoice`.
    # ------------------------------------------------------------------
    @api.model
    def _stripe_id_of(self, value):
        """Devuelve el id tanto si Stripe expandió el objeto como si mandó el string."""
        if isinstance(value, dict):
            return value.get('id')
        return value or False

    @api.model
    def _pi_charge(self, payment_intent):
        """Devuelve el dict del charge de un PaymentIntent, sea cual sea la forma."""
        charges = (payment_intent.get('charges') or {}).get('data') or []
        if charges and isinstance(charges[0], dict):
            return charges[0]
        latest = payment_intent.get('latest_charge')
        if isinstance(latest, dict):
            return latest
        return {}

    @api.model
    def _pi_charge_id(self, payment_intent):
        charge = self._pi_charge(payment_intent)
        if charge.get('id'):
            return charge['id']
        return self._stripe_id_of(payment_intent.get('latest_charge'))

    @api.model
    def _pi_invoice_id(self, payment_intent):
        invoice_id = self._stripe_id_of(payment_intent.get('invoice'))
        if invoice_id:
            return invoice_id
        return self._stripe_id_of(self._pi_charge(payment_intent).get('invoice'))

    @api.model
    def _pi_email(self, payment_intent):
        """Mejor email disponible en un PaymentIntent o Charge."""
        charge = self._pi_charge(payment_intent) or payment_intent
        candidates = [
            (charge.get('billing_details') or {}).get('email'),
            charge.get('receipt_email'),
            payment_intent.get('receipt_email'),
            (payment_intent.get('customer_details') or {}).get('email'),
        ]
        for candidate in candidates:
            if candidate:
                return candidate
        return False

    @api.model
    def _pi_receipt_url(self, payment_intent):
        return self._pi_charge(payment_intent).get('receipt_url') or False

    # ------------------------------------------------------------------
    # Conversión
    # ------------------------------------------------------------------
    @api.model
    def _currency_from_stripe_code(self, code):
        if not code:
            return self.env['res.currency']
        return self.env['res.currency'].sudo().with_context(active_test=False).search(
            [('name', '=', code.upper())], limit=1
        )

    @api.model
    def _amount_from_minor_units(self, amount, currency):
        """Reutiliza el helper del módulo base; nunca dividir por 100 a mano.

        Si la divisa no existe en Odoo, `stripe.sync._amount_from_stripe_minor_units`
        cae a 2 decimales, que es lo correcto para la inmensa mayoría de divisas.
        """
        return self.env['stripe.sync'].sudo()._amount_from_stripe_minor_units(amount, currency)

    @api.model
    def _datetime_from_timestamp(self, timestamp):
        if not timestamp:
            return False
        return fields.Datetime.to_string(datetime.utcfromtimestamp(timestamp))

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------
    @api.model
    def _upsert_from_stripe(self, vals):
        """Crea o actualiza el pago identificado por ``vals['stripe_id']``.

        Semántica **merge, no clobber**:

        - nunca se sobrescribe un campo protegido no vacío con un valor vacío;
        - ``partner_id`` / ``partner_match_method`` solo se pisan si el nuevo método
          tiene confianza mayor o igual que el ya registrado;
        - ``raw_payload`` sí se refresca siempre (queremos la última foto).

        Esto es lo que permite que el mismo pago llegue por varios eventos y por el
        backfill sin duplicarse ni perder información ya resuelta.
        """
        stripe_id = vals.get('stripe_id')
        if not stripe_id:
            _logger.warning("IRG Stripe Payments: upsert sin stripe_id, se ignora: %s", vals)
            return self.browse()

        existing = self.sudo().search([('stripe_id', '=', stripe_id)], limit=1)
        if not existing:
            return self.sudo().create(self._prepare_create_vals(vals))

        update = self._prepare_merge_vals(existing, vals)
        if update:
            existing.write(update)
        return existing

    @api.model
    def _prepare_create_vals(self, vals):
        vals = dict(vals)
        vals.setdefault('partner_state', 'linked' if vals.get('partner_id') else 'unlinked')
        return vals

    @api.model
    def _prepare_merge_vals(self, existing, vals):
        """Calcula el subconjunto de ``vals`` que debe escribirse sobre ``existing``."""
        update = {}
        new_method = vals.get('partner_match_method')

        for field_name, value in vals.items():
            if field_name in ('stripe_id', 'partner_id', 'partner_match_method', 'partner_state'):
                continue
            current = existing[field_name] if field_name in existing._fields else None
            if not value and field_name in self._PROTECTED_FROM_BLANKING:
                continue
            if hasattr(current, 'id'):
                current = current.id
            if current != value:
                update[field_name] = value

        # Identidad: solo se pisa hacia arriba en confianza.
        if vals.get('partner_id'):
            current_score = self.MATCH_CONFIDENCE.get(existing.partner_match_method, -1)
            new_score = self.MATCH_CONFIDENCE.get(new_method, 0)
            if not existing.partner_id or new_score >= current_score:
                if existing.partner_id.id != vals['partner_id']:
                    update['partner_id'] = vals['partner_id']
                if new_method and existing.partner_match_method != new_method:
                    update['partner_match_method'] = new_method
                if existing.partner_state != 'linked':
                    update['partner_state'] = 'linked'
        elif 'partner_state' in vals and not existing.partner_id:
            if existing.partner_state != vals['partner_state']:
                update['partner_state'] = vals['partner_state']

        return update

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    @api.model
    def _cron_irg_stripe_backfill(self):
        """Punto de entrada del cron.

        El motor vive en el AbstractModel ``irg.stripe.backfill``; el cron cuelga de
        este modelo porque ``ir.cron.model_id`` necesita un modelo con tabla.
        """
        return self.env['irg.stripe.backfill'].sudo()._cron_backfill()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def action_open_receipt(self):
        self.ensure_one()
        if not self.receipt_url:
            return False
        return {
            'type': 'ir.actions.act_url',
            'url': self.receipt_url,
            'target': 'new',
        }

    def action_open_review(self):
        self.ensure_one()
        if not self.review_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'irg.stripe.identity.review',
            'res_id': self.review_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_raw_payload(self):
        """Devuelve el payload formateado, útil para soporte."""
        self.ensure_one()
        try:
            return json.dumps(json.loads(self.raw_payload or '{}'), indent=2, sort_keys=True)
        except (TypeError, ValueError):
            return self.raw_payload or ''
