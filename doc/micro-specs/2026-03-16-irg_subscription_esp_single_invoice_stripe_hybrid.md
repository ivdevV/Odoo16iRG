# Micro-spec — IRG Subscription ESP Single Invoice + Stripe Hybrid

## ID
2026-03-16-irg_subscription_esp_single_invoice_stripe_hybrid

## Objetivo
Introducir una nueva estrategia de suscripción para nuevas altas que sustituya el modelo actual de facturación por cuota por un modelo contable español de factura única inicial con desglose de vencimientos. Añadir una base de integración Stripe híbrida configurable por producto, soportando modo tokenizado actual, fallback por link de pago y futuro modo de Stripe Subscription real.

## Alcance
- Nuevo módulo en `addons-extra/extrairg/` para estrategia contable de suscripción.
- Configuración por producto y propagación a `sale.order`.
- Exclusión selectiva del cron legacy de facturación recurrente para la nueva estrategia.
- Wizard de ajuste temporal futuro por porcentaje y duración.
- Tests base Odoo del nuevo módulo.

## Fuera de alcance
- Migración automática masiva de suscripciones existentes.
- Reescritura directa de módulos legacy o core.
- Implementación completa de Stripe Subscription real en esta primera entrega.
- Recalculo retroactivo de cuotas ya facturadas o cobradas.

## Motivación técnica
- Alinear la suscripción con el modelo contable español de factura única y vencimientos.
- Reducir la fragmentación actual entre alta manual y ecommerce.
- Preparar una base segura para evolución posterior de Stripe y ajustes temporales.

## Diseño técnico resumido
- Nuevo módulo: `irg_subscription_esp_single_invoice`.
- Campos nuevos en `product.template` para estrategia contable y modo Stripe.
- Campos nuevos en `sale.order` para snapshot operativo de estrategia.
- Herencia de `_auto_scheduled_order`, `create_subscription_schedule`, `action_confirm` y `_recurring_invoice_domain_update`.
- Nuevo modelo persistente de ajuste temporal y wizard asociado.
- Las cuotas futuras ajustadas guardan trazabilidad de importe original.

## Dependencias
- `sale_subscription`
- `isep_sale_subscription_extension`
- `irg_sale_subscription_esp`
- `irg_checkout_financing_sign_sync`
- `isep_sale_order_cron_payment`
- `irg_payment_stripe_recurring`

## Backwards compatibility / migración
- Primera fase limitada a nuevas suscripciones.
- Convivencia explícita entre estrategia legacy y estrategia nueva.
- La estrategia nueva se activa por configuración de producto y se propaga al pedido.

## Casos de prueba / criterios de aceptación
1. Un producto recurrente configurado con estrategia nueva propaga su configuración al pedido.
2. Un pedido con estrategia nueva queda excluido del dominio del cron legacy de facturación recurrente.
3. El wizard de ajuste temporal reduce únicamente las próximas cuotas no pagadas.
4. El ajuste temporal conserva el importe original para auditoría.
5. La configuración de Stripe queda propagada al pedido para uso posterior por el bridge Stripe.

## Rollback
1. Desinstalar `irg_subscription_esp_single_invoice`.
2. Mantener productos con estrategia legacy por defecto.
3. Volver a ejecutar el flujo operativo normal de módulos existentes.

## Estimación
- Slice inicial: media.
- Rediseño contable completo: alta.
- Integración Stripe real: alta.

## Responsable
GitHub Copilot / implementación asistida.