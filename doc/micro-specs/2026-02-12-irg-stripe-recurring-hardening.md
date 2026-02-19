# Micro-spec — Hardening Stripe Recurring + Checkout/Sign Sync

## ID
2026-02-12-irg-stripe-recurring-hardening

## Objetivo
Consolidar el flujo de suscripciones y cobro recurrente en módulos extra de Odoo 16, asegurando coherencia de estado Stripe, período de gracia, suspensión/reactivación, y trazabilidad operativa en backend.

## Alcance
- Módulo principal: addons-extra/extrairg/irg_payment_stripe_recurring
- Módulo funcional complementario: addons-extra/extrairg/irg_checkout_financing_sign_sync

Incluye:
1. Estado de ciclo de vida Stripe en sale.order (active, past_due, paused, canceled).
2. Trazabilidad de último evento y fecha en sale.order.
3. Período de gracia y cron de aplicación de fin de gracia.
4. Acciones backend en sale.order: Pausar, Reactivar, Cancelar.
5. Persistencia de referencia Stripe para seguimiento interno.
6. Coherencia checkout/report firma (cuota y datos de matrícula) y post-pago de documentación académica.

## Fuera de alcance
- Reescritura del provider payment_stripe nativo.
- Implementación de un dashboard BI dedicado.
- Nuevos endpoints webhook externos no soportados por el flujo actual Odoo.

## Motivación técnica
- Evitar divergencia entre estado de transacción y estado de suscripción comercial.
- Reducir incidencias por impago sin suspensiones tardías.
- Mejorar auditoría operativa para soporte y backoffice.

## Diseño técnico resumido
### irg_payment_stripe_recurring
- Campos nuevos en sale.order para lifecycle Stripe y gracia.
- Hook en payment.transaction.write para mapear transiciones de estado (done/error/cancel) a estado de suscripción.
- Cron nuevo para pausar cuando vence la gracia.
- Vista backend en sale.order con pestaña Stripe Sub y acciones manuales.

### irg_checkout_financing_sign_sync
- Sincronización de cálculo de financiación en checkout.
- Corrección de importes/primer vencimiento en plantilla de matrícula.
- Sección post-pago para subida de documentación académica.
- Pestaña backend para listar adjuntos académicos.

## Riesgos
1. Riesgo de lógica duplicada si otro módulo actualiza estado de suscripción en paralelo.
2. Riesgo de configuración de stages (Suspendida/En curso) por nombre no estandarizado.
3. Riesgo de diferencias por redondeo en cuotas con múltiples monedas.

## Mitigaciones
- Trazabilidad en chatter por cada transición relevante.
- Fallbacks seguros cuando no existe stage objetivo.
- Criterios de aceptación con pruebas de regresión y casos de borde.

## Criterios de aceptación
1. Un pago Stripe exitoso deja la suscripción en estado active y limpia gracia.
2. Un fallo de cobro marca past_due y fecha de gracia.
3. Al vencer gracia, el cron pausa/suspende correctamente.
4. Si se regulariza deuda, reactiva según regla actual.
5. El backend permite pausar/reactivar/cancelar manualmente.
6. Checkout y PDF de matrícula muestran cuota financiada correcta.
7. Se pueden adjuntar documentos académicos post-pago y verlos en backend.

## Rollback
1. Desinstalar irg_checkout_financing_sign_sync si hubiera incidente visual web.
2. Revertir commit de irg_payment_stripe_recurring y actualizar módulo.
3. Desactivar cron nuevo de fin de gracia en caso de comportamiento no deseado.

## Evidencias esperadas
- Capturas de /shop/extra_info, /shop/payment, /shop/confirmation.
- Captura de pestaña Stripe Sub en sale.order.
- Captura de pestaña Doc. académica en sale.order.
- Logs/chatter de transición past_due → paused/active.
