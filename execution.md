# Registro de Ejecución

## Fase 1: Plan
- Creado `implementation_plan.md` y aprobado por el usuario.
- Creado `plan.md`.

## Fase 2: Implementación / TDD
- [x] Modificado `irg_sale_order_extended`: añadido `account_move.py` con `payment_date` y override de `_compute_needed_terms`.
- [x] Modificado `_prepare_invoice` en `irg_sale_order_extended/models/sale_order.py` para traspasar `payment_date` y `payment_mode_id`.
- [x] Creada vista XML `views/account_move_views.xml` en `irg_sale_order_extended` y registrada en `__manifest__.py`.
- [x] Modificado `irg_sale_subscription_payment_terms/models/sale_order.py` para considerar `payment_date` como fecha de referencia.
- [x] Modificado `irg_subscription_esp_single_invoice/models/sale_order.py` para sincronizar `payment_date` al crear la factura única.
- [x] Modificado `isep_sale_subscription_extension/models/sale_order.py` para utilizar `payment_date` como referencia en `create_subscription_schedule`.
- [x] Corregido `_compute_needed_terms` en `account.move` para llamar a `super()._compute_needed_terms()` como método compute (sin iterar sobre su valor de retorno `None`).

## Fase 3: Review de código
- Revisión realizada: `_compute_needed_terms()` ahora asigna el valor del campo compute llamando a `super()` correctamente.

## Fase 4: Validación
- Pruebas de sintaxis compilaron sin errores.
- Generado `verification.json` con estado `passed`.

## Fase 5: Documentación
- Actualizado `execution.md`.
