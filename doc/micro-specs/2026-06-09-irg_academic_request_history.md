# Micro-spec: irg_academic_request_history

## Contexto

El portal academico de certificados y diplomas necesita una base comun para trazar las solicitudes realizadas por alumnos antes de sustituir el pago actual por Stripe Checkout Session. La solicitud existente `irg.certificate.request` ya funciona como registro operativo, pero no contiene todos los campos necesarios para evidencias Stripe ni ofrece historial directo desde contacto y estudiante.

## Decisiones aprobadas

- Se usara Stripe Checkout Session para los pagos de certificados y diplomas.
- Las sesiones de estas solicitudes activaran `invoice_creation[enabled]=true` solo para este flujo.
- Los documentos fisicos podran generar PDF interno y adjuntarse al correo del departamento academico en fases posteriores.
- La Fase 1 no cambia el flujo de pago del portal; solo prepara modelo, historial y vistas backend.

## Alcance Fase 1

- Crear un modulo nuevo por herencia en `addons-extra/extrairg/`.
- Extender `irg.certificate.request` con campos de estudiante, registro de diploma y evidencia Stripe.
- Mostrar los campos de pago/evidencia en la vista backend de solicitudes.
- Anadir smart button de solicitudes academicas en `res.partner`.
- Anadir smart button de solicitudes academicas en `op.student`.
- Mantener compatibilidad con el flujo actual de solicitudes y facturas Odoo.

## Fuera de alcance

- Crear sesiones Stripe Checkout.
- Procesar webhooks Stripe.
- Descargar o adjuntar factura PDF de Stripe.
- Cambiar el comportamiento del portal tras el pago.
- Modificar directamente modulos existentes.

## Validacion esperada

- El modulo instala correctamente en una base Odoo local.
- Los XML de vistas son validos.
- `irg.certificate.request` muestra estudiante, registro de diploma y evidencias Stripe.
- Contactos y estudiantes muestran un smart button con el conteo de solicitudes vinculadas.
- La carga del modulo no rompe el flujo existente de `irg_gradebook_certificates`.
