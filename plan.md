# Plan de Misión: Adaptación de Fechas de Vencimiento de Facturas (payment_date y payment_mode_id)

## Alcance y Clasificación
- **Tier de capacidad**: `standard`
- **Misión**: Ligera (`plan.md`, `execution.md`, `verification.json`)
- **Objetivo**: Garantizar que los vencimientos (`date_maturity`) en los apuntes contables (`account.move.line` 430000 Clientes) de las facturas generadas para suscripciones y pedidos con condiciones de pago (`payment_term_id`) utilicen la fecha de pago (`payment_date`) y el modo de pago (`payment_mode_id`).

## Criterios de Aceptación
1. `account.move` incluye el campo `payment_date`.
2. `sale.order._prepare_invoice()` propaga `payment_date` y `payment_mode_id` a `account.move`.
3. Al calcular los términos/vencimientos en `account.move` (`_compute_needed_terms`), si existe `payment_date`, se utiliza como fecha de referencia (`date_ref`), de modo que las cuotas comiencen a partir de `payment_date`.
4. El cálculo de cronograma de suscripción (`create_subscription_schedule`) respeta `payment_date` en `irg_sale_subscription_payment_terms`, `isep_sale_subscription_extension` e `irg_subscription_esp_single_invoice`.
5. La vista de formulario de factura expone `payment_date`.

## Fases y Propietarios
- **Plan**: Orquestador (Completado)
- **Implementación/TDD**: Codificador
- **Review de código**: Revisor
- **Validación**: Validador
- **Documentación**: Documentador
