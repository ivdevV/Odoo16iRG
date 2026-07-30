# -*- coding: utf-8 -*-
"""Motor de backfill histórico de pagos Stripe.

Se pagina el endpoint ``charges`` y no ``payment_intents``, porque:

- ``charges`` incluye los cobros legacy y de Terminal que no tienen PaymentIntent
  (con ``payment_intents`` serían sencillamente invisibles);
- trae ``amount_refunded`` / ``refunded`` en el propio objeto, sin una segunda llamada;
- trae ``invoice``, ``customer`` y ``billing_details.email``.

Su única desventaja —un PaymentIntent puede tener varios charges tras un reintento—
queda neutralizada porque el ledger se indexa por ``payment_intent or charge_id``, así
que esos charges colapsan en una sola fila.
"""
import logging
import time

from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

CURSOR_PARAM = 'irg_stripe.backfill_cursor'
WINDOW_FROM_PARAM = 'irg_stripe.backfill_window_from'
WINDOW_TO_PARAM = 'irg_stripe.backfill_window_to'
DONE_UNTIL_PARAM = 'irg_stripe.backfill_done_until'
MAX_DAYS_PARAM = 'irg_stripe.backfill_max_days'

DEFAULT_MAX_DAYS = 92
PAGE_SIZE = 100
#: Reintentos por página. `_stripe_make_request` lanza ValidationError ante un 4xx,
#: incluido el 429 de rate limit, así que hay que capturar la excepción y no mirar
#: un supuesto `res['error']`.
BACKOFF_SECONDS = (0.5, 2.0, 8.0)
#: Pausa entre páginas correctas. Muy por debajo del límite de lectura de Stripe.
PAGE_PAUSE_SECONDS = 0.2
#: Páginas entre commits, solo en la ejecución por cron.
COMMIT_EVERY_PAGES = 5


class IrgStripeBackfill(models.AbstractModel):
    _name = 'irg.stripe.backfill'
    _description = 'Backfill de pagos Stripe'

    # ------------------------------------------------------------------
    @api.model
    def _max_days(self):
        try:
            return int(self.env['ir.config_parameter'].sudo().get_param(
                MAX_DAYS_PARAM, DEFAULT_MAX_DAYS))
        except (TypeError, ValueError):
            return DEFAULT_MAX_DAYS

    @api.model
    def _fetch_page(self, provider, endpoint):
        """Una página, con reintentos y backoff exponencial.

        Devuelve el dict de Stripe, o None si la página no se pudo traer tras agotar
        los reintentos: en ese caso el llamante persiste el cursor y termina en
        estado ``partial`` en lugar de propagar la excepción.
        """
        last_error = None
        for attempt, delay in enumerate((0.0,) + BACKOFF_SECONDS):
            if delay:
                time.sleep(delay)
            try:
                res = provider._stripe_make_request(endpoint, method='GET')
            except (ValidationError, UserError) as error:
                last_error = error
                _logger.warning(
                    "IRG Stripe Backfill: fallo al pedir %s (intento %s): %s",
                    endpoint, attempt + 1, error)
                continue
            except Exception as error:  # noqa: BLE001 - la red puede fallar de mil formas
                last_error = error
                _logger.warning(
                    "IRG Stripe Backfill: error inesperado en %s (intento %s): %s",
                    endpoint, attempt + 1, error)
                continue
            if res and res.get('error'):
                last_error = res['error']
                _logger.warning("IRG Stripe Backfill: Stripe devolvió error en %s: %s",
                                endpoint, res['error'])
                continue
            return res

        _logger.error("IRG Stripe Backfill: se agotaron los reintentos en %s: %s",
                      endpoint, last_error)
        return None

    @api.model
    def _build_endpoint(self, mode, ts_from, ts_to, cursor=False, page_size=PAGE_SIZE):
        """Construye el endpoint con los query params EN EL STRING.

        `payment.provider._stripe_make_request` manda `payload` como cuerpo de la
        petición (`data=`), y Stripe ignora el cuerpo en un GET. Por eso la
        paginación tiene que ir aquí y no en `payload`.
        """
        endpoint = f"{mode}?limit={int(page_size)}"
        if ts_from:
            endpoint += f"&created[gte]={int(ts_from)}"
        if ts_to:
            endpoint += f"&created[lte]={int(ts_to)}"
        if cursor:
            endpoint += f"&starting_after={cursor}"
        return endpoint

    # ------------------------------------------------------------------
    @api.model
    def _run(self, provider, ts_from, ts_to, mode='charges', dry_run=False,
             resume=True, commit=False, page_size=PAGE_SIZE):
        """Recorre el rango y hace upsert de cada pago.

        Idempotente: reejecutar el mismo rango no crea filas nuevas ni altera importes,
        porque el ledger está indexado por ``stripe_id`` y el upsert es merge-no-clobber.
        """
        config = self.env['ir.config_parameter'].sudo()
        sync = self.env['stripe.sync'].sudo()
        payment_obj = self.env['irg.stripe.payment'].sudo()

        cursor = config.get_param(CURSOR_PARAM) if resume else False
        summary = {
            'scanned': 0,
            'created': 0,
            'updated': 0,
            'pages': 0,
            'status': 'done',
            'cursor': cursor or False,
        }

        config.set_param(WINDOW_FROM_PARAM, str(int(ts_from)) if ts_from else '')
        config.set_param(WINDOW_TO_PARAM, str(int(ts_to)) if ts_to else '')

        while True:
            endpoint = self._build_endpoint(mode, ts_from, ts_to, cursor, page_size)
            page = self._fetch_page(provider, endpoint)
            if page is None:
                summary['status'] = 'partial'
                config.set_param(CURSOR_PARAM, cursor or '')
                summary['cursor'] = cursor or False
                break

            records = page.get('data') or []
            summary['pages'] += 1
            summary['scanned'] += len(records)

            if not dry_run:
                for record in records:
                    stripe_id = payment_obj._stripe_id_of(record.get('payment_intent')) \
                        or record.get('id')
                    existed = bool(payment_obj.search_count([('stripe_id', '=', stripe_id)]))
                    state = self._state_from_charge(record, payment_obj)
                    sync._irg_upsert_payment(record, origin='backfill', state=state)
                    if existed:
                        summary['updated'] += 1
                    else:
                        summary['created'] += 1

            if not records or not page.get('has_more'):
                config.set_param(CURSOR_PARAM, '')
                config.set_param(DONE_UNTIL_PARAM, str(int(ts_to)) if ts_to else '')
                summary['cursor'] = False
                break

            cursor = records[-1].get('id')
            config.set_param(CURSOR_PARAM, cursor or '')
            summary['cursor'] = cursor

            if commit and summary['pages'] % COMMIT_EVERY_PAGES == 0 \
                    and not self.env.registry.in_test_mode():
                self.env.cr.commit()  # pylint: disable=invalid-commit

            time.sleep(PAGE_PAUSE_SECONDS)

        return summary

    @api.model
    def _state_from_charge(self, charge, payment_obj):
        """Estado de dinero a partir de un Charge del backfill."""
        if charge.get('status') == 'failed':
            return 'failed'
        if not charge.get('amount_refunded'):
            return 'succeeded'
        currency = payment_obj._currency_from_stripe_code(charge.get('currency'))
        refunded = payment_obj._amount_from_minor_units(charge.get('amount_refunded'), currency)
        total = payment_obj._amount_from_minor_units(charge.get('amount') or 0, currency)
        if charge.get('refunded') or (total and refunded >= total):
            return 'refunded'
        return 'partially_refunded'

    # ------------------------------------------------------------------
    @api.model
    def _cron_backfill(self):
        """Ejecución desatendida. Nunca propaga excepciones."""
        config = self.env['ir.config_parameter'].sudo()
        provider = self.env['stripe.sync'].sudo()._get_stripe_provider()
        if not provider:
            _logger.warning("IRG Stripe Backfill: no hay proveedor Stripe activo, se omite.")
            return False

        try:
            ts_from = int(config.get_param(WINDOW_FROM_PARAM) or 0) or False
            ts_to = int(config.get_param(WINDOW_TO_PARAM) or 0) or False
        except (TypeError, ValueError):
            _logger.error("IRG Stripe Backfill: ventana mal configurada, se omite.")
            return False

        if not ts_from or not ts_to:
            _logger.info(
                "IRG Stripe Backfill: sin ventana configurada (%s / %s); nada que hacer.",
                WINDOW_FROM_PARAM, WINDOW_TO_PARAM)
            return False

        summary = self._run(provider, ts_from, ts_to, resume=True, commit=True)
        _logger.info("IRG Stripe Backfill: %s", summary)
        return summary

    @api.model
    def _check_window(self, date_from, date_to):
        if not date_from or not date_to:
            raise UserError(_("Hay que indicar la fecha de inicio y la de fin."))
        if date_from > date_to:
            raise UserError(_("La fecha de inicio no puede ser posterior a la de fin."))
        max_days = self._max_days()
        if (date_to - date_from).days > max_days:
            raise UserError(_(
                "La ventana no puede superar %s días. Trocea el backfill en rangos más "
                "cortos: así una interrupción cuesta menos y el consumo de API de Stripe "
                "queda acotado.") % max_days)
        return True
