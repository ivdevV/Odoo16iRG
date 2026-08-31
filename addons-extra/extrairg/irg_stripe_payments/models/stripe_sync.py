# -*- coding: utf-8 -*-
"""Extensión de ``stripe.sync``: pagos sueltos + resolución de identidad endurecida.

Se apoya en el webhook firmado que ya existe (``/stripe/webhook`` en
``irg_stripe_subscriptions``), del que hereda gratis la verificación HMAC y la
idempotencia por ``stripe.event.log``. **No se crea un endpoint nuevo.**
"""
import json
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

#: Modo de matching por email. Ver README.
EMAIL_MATCH_MODE_PARAM = 'irg_stripe.email_match_mode'


class StripeSync(models.AbstractModel):
    _inherit = 'stripe.sync'

    # ==================================================================
    # Resolución de identidad
    # ==================================================================
    @api.model
    def _irg_email_match_mode(self):
        mode = self.env['ir.config_parameter'].sudo().get_param(
            EMAIL_MATCH_MODE_PARAM, 'strict_unique')
        return mode if mode in ('strict_unique', 'disabled', 'legacy') else 'strict_unique'

    @api.model
    def _irg_partner_extra_domain(self):
        """Excluye los contactos fusionados, si el módulo de merge está instalado."""
        if 'irg_merged_into_partner_id' in self.env['res.partner']._fields:
            return [('irg_merged_into_partner_id', '=', False)]
        return []

    @api.model
    def _resolve_partner(self, customer_id=False, email=False, allow_email_fallback=True,
                         source=False, source_ref=False, log_issues=True):
        """Resuelve el contacto a partir de los datos de Stripe, sin adivinar nunca.

        ``log_issues=False`` deja el encolado en manos del llamante. Es necesario para
        que un mismo evento no genere dos entradas (o infle ``occurrence_count``)
        cuando quien llama también quiere quedarse con la revisión creada.

        Devuelve un diccionario::

            {'partner': <res.partner, 0 o 1 registro>,
             'status': 'matched' | 'ambiguous_email' | 'not_found' | 'no_input'
                       | 'conflicting_customer_id',
             'method': <partner_match_method o False>,
             'candidates': <res.partner recordset>,
             'email': <email normalizado o False>}

        Diferencias con la implementación previa, que hacía ``limit=1`` y escribía el
        customer id sobre el primer contacto que saliera:

        - los archivados y los fusionados quedan fuera;
        - las direcciones hijas (``type`` != contact) y las empresas se despriorizan;
        - **si hay más de un candidato no se elige ninguno**: se devuelve vacío y se
          encola una revisión manual.
        """
        partner_obj = self.env['res.partner'].sudo()
        empty = partner_obj.browse()
        result = {
            'partner': empty,
            'status': 'no_input',
            'method': False,
            'candidates': empty,
            'email': False,
        }

        normalized_email = (email or '').strip().lower()
        result['email'] = normalized_email or False

        if not customer_id and not normalized_email:
            return result

        extra_domain = self._irg_partner_extra_domain()

        # --- 1. Customer ID ya guardado en Odoo -------------------------------
        if customer_id:
            # `irg.stripe.customer` manda: es el único sitio donde una persona puede
            # tener varios Customers. Los dos `Char` se consultan después, para los
            # vínculos que existían antes de que hubiera modelo.
            owner = self.env['irg.stripe.customer']._irg_partner_for(customer_id)
            if owner:
                if extra_domain and not partner_obj.search(
                        [('id', '=', owner.id)] + extra_domain):
                    # El contacto está archivado o fusionado: no es destino válido.
                    owner = partner_obj.browse()
                else:
                    result.update(
                        partner=owner, status='matched', method='stripe_customer_id')
                    return result

            matches = partner_obj.search(
                ['|', ('stripe_customer_id', '=', customer_id),
                      ('irg_stripe_customer_id', '=', customer_id)] + extra_domain
            )
            if len(matches) == 1:
                result.update(partner=matches, status='matched', method='stripe_customer_id')
                return result
            if len(matches) > 1:
                # Antes se cogía el primero en silencio. Eso es exactamente lo que
                # produce pagos vinculados al contacto equivocado.
                result.update(status='conflicting_customer_id', candidates=matches)
                if log_issues:
                    self._log_partner_resolution_issue(
                        result, source=source, source_ref=source_ref, customer_id=customer_id)
                return result

            # --- 2. metadata.odoo_partner_id del Customer en Stripe -----------
            metadata_result = self._irg_partner_from_stripe_customer(customer_id)
            if metadata_result.get('partner'):
                result.update(
                    partner=metadata_result['partner'],
                    status='matched',
                    method='customer_metadata',
                )
                return result
            if metadata_result.get('status') == 'metadata_partner_missing':
                result.update(status='metadata_partner_missing')
                if log_issues:
                    self._log_partner_resolution_issue(
                        result, source=source, source_ref=source_ref, customer_id=customer_id)
                return result
            # El Customer de Stripe puede traer un email que no teníamos.
            if not normalized_email and metadata_result.get('email'):
                normalized_email = metadata_result['email'].strip().lower()
                result['email'] = normalized_email

        # --- 3. Email --------------------------------------------------------
        mode = self._irg_email_match_mode()
        if not allow_email_fallback or mode == 'disabled' or not normalized_email \
                or '@' not in normalized_email:
            if result['status'] == 'no_input':
                result['status'] = 'not_found'
            return result

        if mode == 'legacy':
            # Vía de escape sin redespliegue: restaura el comportamiento antiguo.
            legacy = partner_obj.search([('email', '=ilike', normalized_email)], limit=1)
            if legacy:
                result.update(partner=legacy, status='matched', method='email_unique')
            else:
                result['status'] = 'not_found'
            return result

        # Alumnos primero: en este Odoo `op.student` delega en `res.partner`
        # (_inherits), así que `student.email` ES `partner.email`. Mismo patrón que
        # `irg_student_scholarship_webhook._resolve_partner_by_email`.
        student_domain = [('partner_id.email', '=ilike', normalized_email)]
        student_domain += [('partner_id.%s' % f[0], f[1], f[2]) for f in extra_domain]
        students = self.env['op.student'].sudo().search(student_domain)
        if len(students) == 1:
            result.update(
                partner=students.partner_id, status='matched', method='student_email_unique')
            return result
        if len(students) > 1:
            result.update(status='ambiguous_email', candidates=students.partner_id)
            if log_issues:
                self._log_partner_resolution_issue(
                    result, source=source, source_ref=source_ref, customer_id=customer_id)
            return result

        # Contactos. `active_test` por defecto ya excluye los archivados.
        candidates = partner_obj.search(
            [('email', '=ilike', normalized_email)] + extra_domain)
        narrowed = candidates.filtered(lambda p: p.type == 'contact') or candidates
        narrowed = narrowed.filtered(lambda p: not p.is_company) or narrowed

        if len(narrowed) == 1:
            result.update(partner=narrowed, status='matched', method='email_unique')
            return result
        if len(narrowed) > 1:
            result.update(status='ambiguous_email', candidates=narrowed)
            if log_issues:
                self._log_partner_resolution_issue(
                    result, source=source, source_ref=source_ref, customer_id=customer_id)
            return result

        result['status'] = 'not_found'
        return result

    @api.model
    def _irg_partner_from_stripe_customer(self, customer_id):
        """Consulta el Customer en Stripe y lee ``metadata.odoo_partner_id``."""
        out = {'partner': self.env['res.partner'].browse(), 'email': False, 'status': False}
        provider = self._get_stripe_provider()
        if not provider:
            return out
        try:
            res = provider._stripe_make_request(f"customers/{customer_id}", method='GET')
        except Exception:
            # `_stripe_make_request` lanza ValidationError ante 4xx; no devuelve error.
            _logger.warning(
                "IRG Stripe Payments: no se pudo obtener el Customer %s de Stripe", customer_id)
            return out
        if not res or res.get('error'):
            return out

        out['email'] = res.get('email') or False
        odoo_partner_id = (res.get('metadata') or {}).get('odoo_partner_id')
        if not odoo_partner_id:
            return out

        try:
            partner = self.env['res.partner'].sudo().browse(int(odoo_partner_id)).exists()
        except (TypeError, ValueError):
            return out

        if not partner:
            out['status'] = 'metadata_partner_missing'
            return out
        # Un contacto archivado o fusionado no es un destino válido: es una decisión
        # humana, no algo que debamos resolver solos.
        if not partner.active or (
                'irg_merged_into_partner_id' in partner._fields
                and partner.irg_merged_into_partner_id):
            out['status'] = 'metadata_partner_missing'
            return out

        self._irg_link_customer_id(partner, customer_id)
        out['partner'] = partner
        return out

    @api.model
    def _irg_link_customer_id(self, partner, customer_id, source='auto'):
        """Registra el Customer bajo el contacto. Admite varios por persona.

        Historia de este método, porque explica su forma actual:

        1. La versión original escribía siempre sobre el ``Char``, así que un contacto
           con `cus_A` acababa apuntando a `cus_B` sin dejar rastro.
        2. La corrección siguiente dejó de pisar, pero trataba "este contacto ya tiene
           otro Customer" como un conflicto que encolaba para revisión. Y eso **no es
           un conflicto**: es lo normal. Medido en beta, un contacto tenía cinco
           Customers legítimos, y resolver esas revisiones no hacía nada porque no
           llevaban ningún pago asociado.

        Ahora el único conflicto real es que el Customer ya pertenezca a **otro**
        contacto. Eso sí lo decide una persona.
        """
        if not partner or not customer_id:
            return False

        record, conflict_partner = self.env['irg.stripe.customer']._irg_register(
            partner, customer_id, source=source)

        if conflict_partner:
            self.env['irg.stripe.identity.review'].sudo()._log_issue(
                reason='conflicting_customer_id',
                stripe_object_type='customer',
                stripe_object_id=customer_id,
                stripe_customer_id=customer_id,
                candidates=partner | conflict_partner,
            )
            _logger.warning(
                "IRG Stripe Payments: el Customer %s ya pertenece al contacto %s; no "
                "se reasigna a %s. Encolado para revisión.",
                customer_id, conflict_partner.id, partner.id)
            return False

        return bool(record)

    @api.model
    def _log_partner_resolution_issue(self, result, source=False, source_ref=False,
                                      customer_id=False):
        """Encola la incidencia de identidad. Sobrescribe el seam del módulo base."""
        reason = result.get('status')
        if reason not in ('ambiguous_email', 'not_found', 'conflicting_customer_id',
                          'metadata_partner_missing'):
            return self.env['irg.stripe.identity.review'].browse()
        return self.env['irg.stripe.identity.review'].sudo()._log_issue(
            reason=reason,
            stripe_object_type=source or False,
            stripe_object_id=source_ref or False,
            stripe_customer_id=customer_id or False,
            stripe_email=result.get('email') or False,
            candidates=result.get('candidates'),
        )

    @api.model
    def _find_partner(self, customer_id, email=False):
        """Firma idéntica a la del módulo base; ahora sin adivinar.

        Los llamantes existentes (`_sync_subscription_object`, `_sync_checkout_session`)
        siguen funcionando: ambos tratan el recordset vacío correctamente. El único
        cambio de comportamiento es que ante ambigüedad se devuelve vacío en lugar de
        un contacto elegido al azar.
        """
        result = self._resolve_partner(customer_id, email=email, source='customer',
                                       source_ref=customer_id)
        partner = result['partner']
        if partner and customer_id:
            self._irg_link_customer_id(partner, customer_id)
        return partner

    # ==================================================================
    # Identidad de un pago concreto
    # ==================================================================
    @api.model
    def _irg_identify_payment(self, stripe_id, payment_intent_id=False, customer_id=False,
                              email=False, metadata=None, client_reference_id=False,
                              object_type='payment_intent'):
        """Resuelve contacto y documentos comerciales de un pago.

        Escalera, de más fiable a menos. Las tres primeras vías son deterministas: no
        dependen del email y por tanto no pueden equivocarse de persona.
        """
        metadata = metadata or {}
        partner_obj = self.env['res.partner'].sudo()
        out = {
            'partner': partner_obj.browse(),
            'method': False,
            'sale_order': self.env['sale.order'].browse(),
            'transaction': self.env['payment.transaction'].browse(),
            'move': self.env['account.move'].browse(),
            'review': self.env['irg.stripe.identity.review'].browse(),
        }

        # --- 1. La transacción de pago de Odoo (máxima confianza) -------------
        reference = payment_intent_id or stripe_id
        if reference:
            tx = self.env['payment.transaction'].sudo().search(
                [('provider_reference', '=', reference)], limit=1)
            if tx:
                out['transaction'] = tx
                out['sale_order'] = tx.sale_order_ids[:1]
                out['move'] = tx.invoice_ids[:1]
                if tx.partner_id:
                    out['partner'] = tx.partner_id
                    out['method'] = 'payment_transaction'
                    return out

        # --- 2. client_reference_id -------------------------------------------
        order = self._irg_order_from_client_reference(client_reference_id)
        if order:
            out['sale_order'] = order
            out['partner'] = order.partner_id
            out['method'] = 'client_reference_id'
            return out
        partner = self._irg_partner_from_client_reference(client_reference_id)
        if partner:
            out['partner'] = partner
            out['method'] = 'client_reference_id'
            return out

        # --- 3. metadata del objeto -------------------------------------------
        if metadata.get('odoo_order_id'):
            try:
                order = self.env['sale.order'].sudo().browse(
                    int(metadata['odoo_order_id'])).exists()
            except (TypeError, ValueError):
                order = self.env['sale.order'].browse()
            if order:
                out['sale_order'] = order
                out['partner'] = order.partner_id
                out['method'] = 'object_metadata'
                return out
        if metadata.get('odoo_partner_id'):
            try:
                partner = partner_obj.browse(int(metadata['odoo_partner_id'])).exists()
            except (TypeError, ValueError):
                partner = partner_obj.browse()
            if partner:
                out['partner'] = partner
                out['method'] = 'object_metadata'
                return out

        # --- 4. Customer ID / metadata del Customer / email --------------------
        result = self._resolve_partner(
            customer_id, email=email, source=object_type, source_ref=stripe_id,
            log_issues=False)
        if result['partner']:
            out['partner'] = result['partner']
            out['method'] = result['method']
            if customer_id:
                self._irg_link_customer_id(result['partner'], customer_id)
        else:
            out['review'] = self._log_partner_resolution_issue(
                result, source=object_type, source_ref=stripe_id, customer_id=customer_id)
        return out

    @api.model
    def _irg_order_from_client_reference(self, client_reference_id):
        if not client_reference_id or not client_reference_id.startswith('odoo_order_'):
            return self.env['sale.order'].browse()
        try:
            order_id = int(client_reference_id[len('odoo_order_'):])
        except (TypeError, ValueError):
            return self.env['sale.order'].browse()
        return self.env['sale.order'].sudo().browse(order_id).exists()

    @api.model
    def _irg_partner_from_client_reference(self, client_reference_id):
        if not client_reference_id or not client_reference_id.startswith('odoo_partner_'):
            return self.env['res.partner'].browse()
        try:
            partner_id = int(client_reference_id[len('odoo_partner_'):])
        except (TypeError, ValueError):
            return self.env['res.partner'].browse()
        return self.env['res.partner'].sudo().browse(partner_id).exists()

    # ==================================================================
    # Construcción de la fila del ledger
    # ==================================================================
    @api.model
    def _irg_payment_vals_from_payment_intent(self, obj, origin='webhook', state='succeeded',
                                              client_reference_id=False,
                                              checkout_session_id=False,
                                              extra_metadata=None):
        """Traduce un PaymentIntent (o Charge) de Stripe a valores del ledger."""
        payment_model = self.env['irg.stripe.payment'].sudo()

        payment_intent_id = obj.get('id') if (obj.get('object') != 'charge') else \
            payment_model._stripe_id_of(obj.get('payment_intent'))
        charge_id = obj.get('id') if obj.get('object') == 'charge' else \
            payment_model._pi_charge_id(obj)
        # Ancla de idempotencia: el PaymentIntent manda; si no hay (charges legacy o
        # de Terminal), el propio Charge. Así varios charges de un mismo PI —los que
        # produce un reintento— colapsan en una única fila.
        stripe_id = payment_intent_id or charge_id
        if not stripe_id:
            return {}

        metadata = dict(obj.get('metadata') or {})
        if extra_metadata:
            metadata.update({k: v for k, v in extra_metadata.items() if v})

        currency_code = obj.get('currency')
        currency = payment_model._currency_from_stripe_code(currency_code)
        amount = payment_model._amount_from_minor_units(
            obj.get('amount_received') if obj.get('amount_received') is not None
            else obj.get('amount'), currency)
        amount_refunded = payment_model._amount_from_minor_units(
            obj.get('amount_refunded') or 0, currency)

        invoice_id = payment_model._pi_invoice_id(obj) if obj.get('object') != 'charge' \
            else payment_model._stripe_id_of(obj.get('invoice'))
        customer_id = payment_model._stripe_id_of(obj.get('customer'))
        email = payment_model._pi_email(obj)

        identity = self._irg_identify_payment(
            stripe_id,
            payment_intent_id=payment_intent_id,
            customer_id=customer_id,
            email=email,
            metadata=metadata,
            client_reference_id=client_reference_id,
            object_type='charge' if obj.get('object') == 'charge' else 'payment_intent',
        )

        subscription = self.env['stripe.subscription'].browse()
        if invoice_id:
            subscription = self._irg_subscription_from_invoice_id(invoice_id)

        vals = {
            'stripe_id': stripe_id,
            'stripe_payment_intent_id': payment_intent_id or False,
            'stripe_charge_id': charge_id or False,
            'stripe_checkout_session_id': checkout_session_id or False,
            'stripe_invoice_id': invoice_id or False,
            'stripe_customer_id': customer_id or False,
            'stripe_customer_email': email or False,
            'state': state,
            'amount': amount,
            'amount_refunded': amount_refunded,
            'currency_id': currency.id if currency else False,
            'stripe_currency': (currency_code or '').upper() or False,
            'payment_date': payment_model._datetime_from_timestamp(obj.get('created')),
            'description': obj.get('description') or False,
            'receipt_url': payment_model._pi_receipt_url(obj)
            or (obj.get('receipt_url') if obj.get('object') == 'charge' else False),
            'origin': origin,
            'partner_id': identity['partner'].id if identity['partner'] else False,
            'partner_match_method': identity['method'] or False,
            'partner_state': 'linked' if identity['partner']
            else ('review' if identity['review'] else 'unlinked'),
            'review_id': identity['review'].id if identity['review'] else False,
            'sale_order_id': identity['sale_order'].id if identity['sale_order'] else False,
            'move_id': identity['move'].id if identity['move'] else False,
            'payment_transaction_id': identity['transaction'].id if identity['transaction'] else False,
            'stripe_subscription_id': subscription.id if subscription else False,
            'raw_payload': json.dumps(obj, indent=2, sort_keys=True, default=str),
        }
        return vals

    @api.model
    def _irg_subscription_from_invoice_id(self, invoice_id):
        return self.env['stripe.subscription'].sudo().search(
            [('latest_invoice_id', '=', invoice_id)], limit=1)

    @api.model
    def _irg_upsert_payment(self, obj, origin='webhook', state='succeeded',
                            client_reference_id=False, checkout_session_id=False,
                            extra_metadata=None):
        vals = self._irg_payment_vals_from_payment_intent(
            obj, origin=origin, state=state, client_reference_id=client_reference_id,
            checkout_session_id=checkout_session_id, extra_metadata=extra_metadata)
        if not vals:
            return self.env['irg.stripe.payment'].browse()
        return self.env['irg.stripe.payment'].sudo()._upsert_from_stripe(vals)

    # ==================================================================
    # Eventos
    # ==================================================================
    @api.model
    def dispatch_event(self, event_data):
        """Añade los tipos de evento que el módulo base no contempla.

        Deliberadamente NO se suscribe `charge.succeeded`: en un pago con tarjeta
        normal lleva `payment_intent` y es duplicado estricto de
        `payment_intent.succeeded`. Los charges sin PaymentIntent (legacy, Terminal)
        los recoge el backfill, que pagina el endpoint `charges`.
        """
        event_type = event_data.get('type')
        event_obj = (event_data.get('data') or {}).get('object') or {}

        if event_type == 'payment_intent.payment_failed':
            self._irg_sync_payment_intent_failed(event_obj)
            return
        if event_type == 'charge.refunded':
            self._irg_sync_charge_refunded(event_obj)
            return

        return super().dispatch_event(event_data)

    @api.model
    def _sync_payment_intent_succeeded(self, payment_intent_obj):
        """Registra SIEMPRE el pago, tenga o no factura de Stripe asociada.

        El módulo base salía por `return` cuando no había `invoice`, que es
        justamente el caso de todo pago suelto (Payment Link de pago único, cobro
        desde el Dashboard, Checkout puntual, Terminal). Por eso no había nada que
        listar.

        El upsert va ANTES del `super()`, y el `super()` conserva intacta la
        delegación a `_sync_invoice_paid` para los pagos de suscripción. El ledger no
        concilia, así que no puede haber doble conteo.
        """
        self._irg_upsert_payment(payment_intent_obj, origin='webhook', state='succeeded')
        return super()._sync_payment_intent_succeeded(payment_intent_obj)

    @api.model
    def _irg_sync_payment_intent_failed(self, payment_intent_obj):
        """Un pago fallido es información de soporte, no de contabilidad."""
        self._irg_upsert_payment(payment_intent_obj, origin='webhook', state='failed')

    @api.model
    def _irg_sync_charge_refunded(self, charge_obj):
        """Actualiza el reembolso sobre la fila existente.

        Los eventos de PaymentIntent no disparan al reembolsar: sin este handler el
        listado seguiría mostrando el importe original para siempre.
        """
        payment_model = self.env['irg.stripe.payment'].sudo()
        currency = payment_model._currency_from_stripe_code(charge_obj.get('currency'))
        refunded = payment_model._amount_from_minor_units(
            charge_obj.get('amount_refunded') or 0, currency)
        total = payment_model._amount_from_minor_units(charge_obj.get('amount') or 0, currency)
        state = 'refunded' if charge_obj.get('refunded') or (
            total and refunded >= total) else 'partially_refunded'

        payment = self._irg_upsert_payment(charge_obj, origin='webhook', state=state)
        if payment:
            payment.write({'amount_refunded': refunded, 'state': state})
        return payment

    @api.model
    def _sync_checkout_session(self, session_obj):
        """Registra el pago de una Checkout Session de pago único.

        El upsert va ANTES del `super()` a propósito: `irg_campus_certificates_portal`
        también extiende este método y hace `return` temprano para las sesiones de
        certificado. Si dependiéramos del `super()`, esos pagos nunca llegarían al
        ledger según el orden del MRO.
        """
        if (session_obj.get('mode') or 'payment') == 'payment':
            payment_intent_id = self.env['irg.stripe.payment'].sudo()._stripe_id_of(
                session_obj.get('payment_intent'))
            if payment_intent_id:
                self._irg_upsert_payment_from_session(session_obj, payment_intent_id)

        return super()._sync_checkout_session(session_obj)

    @api.model
    def _irg_upsert_payment_from_session(self, session_obj, payment_intent_id):
        """La sesión trae la mejor señal de identidad; el PaymentIntent a menudo ninguna."""
        provider = self._get_stripe_provider()
        payment_intent_obj = {}
        if provider:
            try:
                res = provider._stripe_make_request(
                    f"payment_intents/{payment_intent_id}", method='GET')
                if res and not res.get('error'):
                    payment_intent_obj = res
            except Exception:
                _logger.warning(
                    "IRG Stripe Payments: no se pudo obtener el PaymentIntent %s de Stripe",
                    payment_intent_id)

        if not payment_intent_obj:
            # Construimos lo mínimo con lo que trae la propia sesión.
            payment_intent_obj = {
                'id': payment_intent_id,
                'object': 'payment_intent',
                'amount': session_obj.get('amount_total'),
                'currency': session_obj.get('currency'),
                'customer': session_obj.get('customer'),
                'created': session_obj.get('created'),
                'metadata': session_obj.get('metadata') or {},
                'customer_details': session_obj.get('customer_details') or {},
            }

        return self._irg_upsert_payment(
            payment_intent_obj,
            origin='webhook',
            state='succeeded',
            client_reference_id=session_obj.get('client_reference_id'),
            checkout_session_id=session_obj.get('id'),
            extra_metadata=session_obj.get('metadata') or {},
        )
