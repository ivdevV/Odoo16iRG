# -*- coding: utf-8 -*-
"""Cola de revisión manual de identidad.

Existe como modelo propio, y no como un simple estado sobre ``irg.stripe.payment``,
porque la ambigüedad de identidad también ocurre en eventos que no producen ninguna
fila de pago suelto (``customer.subscription.*``, ``checkout.session.completed`` de
suscripción). Ese es justamente el caso que antes se resolvía adivinando en silencio.
"""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrgStripeIdentityReview(models.Model):
    _name = 'irg.stripe.identity.review'
    _description = 'Revisión de identidad Stripe'
    _order = 'state, last_seen_at desc, id desc'

    name = fields.Char(string='Resumen', compute='_compute_name', store=True)
    reason = fields.Selection(
        [
            ('ambiguous_email', 'Email ambiguo'),
            ('not_found', 'Contacto no encontrado'),
            ('conflicting_customer_id', 'Customer ID en conflicto'),
            ('metadata_partner_missing', 'Partner de la metadata inexistente'),
        ],
        string='Motivo',
        required=True,
        index=True,
    )
    stripe_object_type = fields.Selection(
        [
            ('payment_intent', 'PaymentIntent'),
            ('charge', 'Charge'),
            ('checkout_session', 'Checkout Session'),
            ('subscription', 'Suscripción'),
            ('customer', 'Customer'),
        ],
        string='Tipo de objeto',
    )
    stripe_object_id = fields.Char(string='ID objeto Stripe', index=True)
    stripe_customer_id = fields.Char(string='Customer Stripe', index=True)
    stripe_email = fields.Char(string='Email en Stripe', index=True)

    candidate_partner_ids = fields.Many2many(
        'res.partner',
        'irg_stripe_review_candidate_rel',
        'review_id',
        'partner_id',
        string='Candidatos',
        help="Contactos entre los que el sistema se negó a elegir. Vaciar esta lista no "
             "resuelve nada: hay que seleccionar un contacto o ignorar la revisión.",
    )
    partner_id = fields.Many2one('res.partner', string='Contacto asignado', ondelete='restrict')

    state = fields.Selection(
        [
            ('open', 'Abierta'),
            ('resolved', 'Resuelta'),
            ('ignored', 'Ignorada'),
        ],
        string='Estado',
        default='open',
        required=True,
        index=True,
    )
    resolution_note = fields.Text(string='Nota de resolución')
    resolved_by_id = fields.Many2one('res.users', string='Resuelta por', readonly=True)
    resolved_at = fields.Datetime(string='Resuelta el', readonly=True)

    occurrence_count = fields.Integer(string='Ocurrencias', default=1, readonly=True)
    last_seen_at = fields.Datetime(string='Visto por última vez', default=fields.Datetime.now)

    payment_ids = fields.One2many('irg.stripe.payment', 'review_id', string='Pagos afectados')
    payment_count = fields.Integer(string='Nº de pagos', compute='_compute_payment_count')

    @api.depends('reason', 'stripe_customer_id', 'stripe_email', 'candidate_partner_ids')
    def _compute_name(self):
        for review in self:
            parts = [review.stripe_customer_id or review.stripe_object_id or '?']
            if review.stripe_email:
                parts.append(review.stripe_email)
            if review.reason == 'ambiguous_email':
                parts.append(_("%s candidatos") % len(review.candidate_partner_ids))
            elif review.reason:
                parts.append(dict(self._fields['reason'].selection).get(review.reason, review.reason))
            review.name = ' · '.join(parts)

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for review in self:
            review.payment_count = len(review.payment_ids)

    # ------------------------------------------------------------------
    @api.model
    def _log_issue(self, reason, stripe_object_type=False, stripe_object_id=False,
                   stripe_customer_id=False, stripe_email=False, candidates=None):
        """Encola una incidencia de identidad, agrupando por objeto + motivo.

        Un mismo Customer que reintenta muchas veces no debe generar una fila por
        evento: se sube ``occurrence_count`` sobre la revisión abierta existente.
        """
        domain = [('reason', '=', reason), ('state', '=', 'open')]
        if stripe_object_id:
            domain.append(('stripe_object_id', '=', stripe_object_id))
        elif stripe_customer_id:
            domain.append(('stripe_customer_id', '=', stripe_customer_id))
        elif stripe_email:
            domain.append(('stripe_email', '=', stripe_email))
        else:
            _logger.warning(
                "IRG Stripe Payments: incidencia de identidad '%s' sin ningún "
                "identificador con el que agrupar; no se encola.", reason)
            return self.browse()

        review = self.sudo().search(domain, limit=1)
        candidate_ids = candidates.ids if candidates else []
        if review:
            vals = {
                'occurrence_count': review.occurrence_count + 1,
                'last_seen_at': fields.Datetime.now(),
            }
            if candidate_ids:
                vals['candidate_partner_ids'] = [fields.Command.set(candidate_ids)]
            review.write(vals)
            return review

        return self.sudo().create({
            'reason': reason,
            'stripe_object_type': stripe_object_type or False,
            'stripe_object_id': stripe_object_id or False,
            'stripe_customer_id': stripe_customer_id or False,
            'stripe_email': stripe_email or False,
            'candidate_partner_ids': [fields.Command.set(candidate_ids)] if candidate_ids else False,
        })

    # ------------------------------------------------------------------
    def action_open_link_wizard(self):
        self.ensure_one()
        self._check_can_resolve()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'irg.stripe.identity.link.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_review_id': self.id},
        }

    def action_ignore(self):
        for review in self:
            review._check_can_resolve()
            if not review.resolution_note:
                raise UserError(_(
                    "Para ignorar una revisión hay que dejar escrito el porqué en la "
                    "nota de resolución."))
            review.write({
                'state': 'ignored',
                'resolved_by_id': self.env.user.id,
                'resolved_at': fields.Datetime.now(),
            })
        return True

    def action_reopen(self):
        self._check_can_resolve()
        self.write({'state': 'open', 'resolved_by_id': False, 'resolved_at': False})
        return True

    def _check_can_resolve(self):
        """Control de acceso en servidor.

        La visibilidad del botón en la vista no es un control de seguridad: un usuario
        puede invocar el método por RPC. Se comprueba aquí, no en el XML.
        """
        self.check_access_rights('write')
        self.check_access_rule('write')

    def action_view_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Pagos afectados"),
            'res_model': 'irg.stripe.payment',
            'view_mode': 'tree,form',
            'domain': [('review_id', '=', self.id)],
        }
