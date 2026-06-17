# Micro-spec: Fase 2 generadores y control de pagos academicos

## Contexto

La Fase 1 preparo el historial comun de solicitudes academicas sobre `irg.certificate.request`. Antes de conectar Stripe Checkout, el sistema debe garantizar que cada solicitud pueda generar su documento correctamente y que el alumno cumple las condiciones economicas para solicitarlo.

## Alcance

- Hacer obligatoria la dependencia de `irg_certificate_partial` para asegurar que `gradebook_partial` tiene generador disponible.
- Vincular los diplomas generados desde solicitudes con `irg.diploma.registry`.
- Guardar el PDF generado del diploma en `irg.diploma.registry.attachment_id`.
- Guardar el registro de diploma en `irg.certificate.request.diploma_registry_id`.
- Centralizar la validacion de pagos academicos del alumno.
- Bloquear solicitudes de portal no elegibles.
- Bloquear generacion backend y procesado post-pago si el alumno no cumple pagos.
- Registrar estado, fecha y motivo de validacion en la solicitud.

## Reglas De Pago

- `gradebook` y `diploma`: requieren que el master/programa este completamente pagado.
- `gradebook_partial`, `attendance` y `enrollment`: requieren que el alumno no tenga deuda academica vencida.
- Si no hay informacion de venta/facturacion para un `gradebook` final o `diploma`, se bloquea porque no se puede comprobar que el master este pagado.

## Fuentes De Validacion

- Pedidos `sale.order` vinculados al alumno por `student_id` o `partner_id`.
- Lineas de cronograma `subscription_schedule`, cuando existen.
- Facturas `account.move` publicadas vinculadas por `partner_id` o `irg_student_partner_id`.
- Metodo existente `op.student.get_subscription_data()`, cuando esta disponible.

## Fuera De Alcance

- Crear Stripe Checkout Session.
- Procesar webhooks Stripe.
- Enviar emails automaticos al departamento academico.
- Adjuntar factura Stripe al expediente.

## Validacion Esperada

- El modulo instala/actualiza correctamente en Odoo local.
- Las vistas XML son validas.
- Las solicitudes finales de portal sin evidencia de pago completo se bloquean.
- Las solicitudes parciales pueden pasar si no hay deuda vencida.
- El generador de diploma deja enlazados solicitud, registro de diploma y PDF.
