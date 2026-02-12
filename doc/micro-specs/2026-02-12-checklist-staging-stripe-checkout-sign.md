# Checklist de validación staging — Stripe + Checkout + Firma

## Preparación
- Actualizar módulos:
  - irg_payment_stripe_recurring
  - irg_checkout_financing_sign_sync
- Verificar que los 3 cron de irg_payment_stripe_recurring existen:
  1. Verificar suscripciones con cuotas vencidas
  2. Reactivar suscripciones pagadas
  3. Aplicar fin de gracia Stripe

## A. Checkout financiación
1. Usuario no logueado:
   - Revisar pedido muestra línea de gastos de financiación.
   - 1ra cuota y cuotas restantes reflejan precio financiado, no contado.
2. Usuario logueado:
   - Repetir validación anterior y comprobar mismo resultado.
3. Pantallas:
   - /shop/extra_info
   - /shop/payment

## B. Documento de matrícula para firma
1. Generar documento y comprobar campos:
   - DNI/Pasaporte
   - Móvil
   - Estudios
   - Universidad
   - Año graduación
   - Profesión
   - Asesor
   - Matrícula/Pago Inicial
   - Forma de Pago
   - Primer Vencimiento
2. Confirmar que Matrícula/Pago Inicial refleja primera cuota financiada.
3. Confirmar que Primer Vencimiento toma la primera línea real de schedule.

## C. Post-pago documentación académica
1. En /shop/confirmation aparece bloque de Documentación académica.
2. Subir 1+ archivos válidos (pdf/jpg/png/doc/docx).
3. Confirmar mensaje de éxito.
4. En sale.order:
   - Ver adjuntos en chatter.
   - Ver adjuntos en pestaña Doc. académica.

## D. Stripe lifecycle en backend
1. En sale.order (suscripción) validar pestaña Stripe Sub:
   - stripe_subscription_state
   - stripe_subscription_ref
   - stripe_last_event
   - stripe_last_event_at
   - stripe_grace_until
2. Simular pago exitoso:
   - Estado pasa a active.
   - Se limpia gracia.
3. Simular fallo de cobro:
   - Estado pasa a past_due.
   - Se informa stripe_grace_until.
4. Ejecutar cron Aplicar fin de gracia con fecha vencida:
   - Estado pasa a paused.
   - subscription_suspended = true.
5. Ejecutar cron Reactivar tras regularización:
   - Estado vuelve a active.
   - subscription_suspended = false.
6. Botones manuales:
   - Pausar
   - Reactivar
   - Cancelar

## E. Regresión mínima
- No rompe envío a firma existente.
- No rompe creación de payment.transaction.
- No rompe cron previo de cobro tokenizado.

## Resultado final (go/no-go)
- GO si todos los ítems críticos A1/A2/B2/B3/C4/D2/D3/D4 pasan.
- NO-GO si cualquier ítem crítico falla.
