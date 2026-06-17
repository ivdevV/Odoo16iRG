# irg_academic_request_history

## Ficha Tecnica

| Propiedad | Valor |
| --- | --- |
| Nombre tecnico | `irg_academic_request_history` |
| Version | `16.0.1.0.0` |
| Categoria | Education |
| Licencia | LGPL-3 |
| Autor | iRG |
| Tipo | Modulo de herencia |

## Dependencias

- `irg_gradebook_certificates`
- `irg_generacion_diplomas`
- `irg_campus_certificates_portal`
- `irg_certificate_partial`
- `irg_student_invoice_payment_link`
- `openeducat_core`

## Proposito

Este modulo prepara la Fase 1 del flujo de solicitudes academicas del portal. Extiende `irg.certificate.request` para convertirlo en el registro unico de historial y trazabilidad de certificados y diplomas solicitados por alumnos.

Tambien incorpora la Fase 2: dependencias de generadores, vinculo entre solicitudes y diplomas generados, y validacion economica previa a solicitudes/generacion. Los pagos por Stripe Checkout Session, webhooks y paginas post-pago se implementaran en fases posteriores.

## Cambios En Modelos

### `irg.certificate.request`

Campos academicos:

| Campo | Tipo | Uso |
| --- | --- | --- |
| `student_id` | Many2one `op.student` | Estudiante vinculado a la solicitud. Se calcula desde la libreta o desde el partner. |
| `diploma_registry_id` | Many2one `irg.diploma.registry` | Registro interno de diploma que se vinculara cuando una solicitud genere diploma. |

Campos de pago y evidencia Stripe:

| Campo | Tipo | Uso |
| --- | --- | --- |
| `payment_amount` | Monetary | Importe pagado o preparado para pago. |
| `payment_currency_id` | Many2one `res.currency` | Moneda del pago. |
| `payment_concept` | Char | Concepto visible para la evidencia de pago. |
| `payment_success_date` | Datetime | Fecha de confirmacion del pago. |
| `stripe_checkout_session_id` | Char | ID de Stripe Checkout Session (`cs_...`). |
| `stripe_payment_intent_id` | Char | ID de PaymentIntent (`pi_...`). |
| `stripe_invoice_id` | Char | ID de factura Stripe (`in_...`). |
| `stripe_invoice_url` | Char | URL hospedada de factura Stripe. |
| `stripe_invoice_pdf` | Char | URL del PDF de factura Stripe. |
| `stripe_receipt_url` | Char | URL del recibo Stripe. |
| `stripe_payment_status` | Char | Estado de pago reportado por Stripe. |

Campos de validacion academica/economica:

| Campo | Tipo | Uso |
| --- | --- | --- |
| `academic_payment_validation_state` | Selection | Estado de validacion: no comprobado, apto o bloqueado. |
| `academic_payment_validation_date` | Datetime | Fecha de la ultima validacion de pagos. |
| `academic_payment_block_reason` | Text | Motivo legible cuando la solicitud queda bloqueada. |

### `res.partner`

- `academic_request_count`: contador de solicitudes academicas vinculadas al contacto.
- `action_view_academic_requests()`: abre la accion de solicitudes filtrada por `partner_id`.

### `op.student`

- `academic_request_count`: contador de solicitudes academicas vinculadas al estudiante o a su partner.
- `action_view_academic_requests()`: abre la accion de solicitudes filtrada por `student_id` o `partner_id`.

## Cambios En Vistas

### Solicitudes Academicas

La vista backend de `irg.certificate.request` anade:

- Campo `student_id` en datos del alumno.
- Campo `diploma_registry_id` en la pestana de documentos cuando el tipo es diploma.
- Pestana `Validacion Academica` con estado, fecha y motivo de bloqueo por pagos.
- Pestana `Pago Stripe` con resumen de pago y evidencias Stripe.
- Columnas opcionales en lista para estudiante, fecha de pago y estado Stripe.
- Columna opcional y filtro para bloqueos de pago del alumno.
- Busqueda por estudiante, Stripe Session y PaymentIntent.
- Filtro `Pagado Stripe` y agrupacion por estudiante.

## Fase 2: Generadores Y Pagos

### Dependencias De Generacion

`irg_certificate_partial` pasa a ser dependencia obligatoria para que el tipo `gradebook_partial` tenga generador disponible siempre que el portal lo ofrezca.

### Vinculo De Diplomas

Cuando una solicitud de tipo `diploma` genera PDF:

- Se ejecuta el generador existente de `irg_gradebook_certificates`/`irg_generacion_diplomas`.
- Se localiza el nuevo `irg.diploma.registry` creado durante la generacion.
- Se escribe el PDF generado en `irg.diploma.registry.attachment_id`.
- Se escribe el registro en `irg.certificate.request.diploma_registry_id`.

Esto permite que el portal descargue diplomas desde `irg.diploma.registry` y que la solicitud mantenga trazabilidad del documento generado.

### Validacion De Pagos

El metodo central `_check_academic_payment_eligibility()` valida si una solicitud puede avanzar.

Fuentes utilizadas:

- `sale.order` por `student_id` o `partner_id` del alumno.
- Cronograma `subscription_schedule` si existe en el pedido.
- Facturas `account.move` publicadas por `partner_id` o `irg_student_partner_id`.
- `op.student.get_subscription_data()` si esta disponible.

Reglas:

- `gradebook` y `diploma` requieren master/programa completamente pagado.
- `gradebook_partial`, `attendance` y `enrollment` requieren no tener deuda academica vencida.
- Si no hay ventas/facturas para comprobar un documento final o diploma, se bloquea por falta de evidencia economica.

Puntos de aplicacion:

- Creacion de solicitudes de portal.
- Generacion backend mediante `action_generate_pdf()`.
- Procesado post-pago mediante `_process_payment()`.

### Contactos

La ficha de `res.partner` muestra siempre un smart button `Solicitudes`, incluso cuando el contador es `0`, para permitir acceder al historial filtrado desde el contacto.

### Estudiantes

La ficha de `op.student` muestra siempre un smart button `Solicitudes`, incluso cuando el contador es `0`, para permitir acceder al historial filtrado desde el estudiante.

## Decisiones De Diseno

- Se crea un modulo nuevo para cumplir la regla del proyecto de no modificar directamente modulos existentes.
- `student_id` es almacenado e indexado para facilitar busquedas e historiales.
- Los campos Stripe quedan de solo lectura porque se rellenaran desde el flujo de Checkout/Webhook en fases posteriores.
- No se crean modelos nuevos, por lo que no se anaden ACLs propias.

## Validacion Realizada

Comandos ejecutados:

```bash
python3 -m compileall addons-extra/extrairg/irg_academic_request_history
```

```bash
python3 - <<'PY'
from pathlib import Path
from xml.etree import ElementTree as ET
for path in Path('addons-extra/extrairg/irg_academic_request_history/views').glob('*.xml'):
    ET.parse(path)
    print(f'XML OK: {path}')
PY
```

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_academic_request_history --stop-after-init --log-level=test
```

Resultado:

- Compilacion Python correcta.
- XML correcto.
- Instalacion del modulo correcta en `test_irg_db`.
- Las advertencias emitidas durante la carga pertenecen al entorno y a modulos preexistentes; no bloquearon la instalacion del modulo.

Validacion Fase 2:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_academic_request_history --test-enable --stop-after-init --log-level=test
```

Resultado Fase 2:

- Actualizacion correcta del modulo en `test_irg_db`.
- Tests del modulo ejecutados correctamente.
- Resultado Odoo: `0 failed, 0 error(s)`.

## Limitaciones Conocidas

- Los campos Stripe se preparan pero no se rellenan todavia.
- La validacion economica usa las fuentes disponibles en Odoo; si un documento final no tiene evidencia de venta/factura, se bloquea por seguridad.
- El portal sigue usando el flujo de pago existente hasta las fases de Stripe Checkout.

## Changelog

- **2026-06-09:** Creacion del modulo de Fase 1 con trazabilidad de solicitudes academicas, campos de evidencia Stripe y smart buttons en contacto/estudiante.
- **2026-06-09:** Ajuste de visibilidad para mostrar siempre el smart button `Solicitudes` en contactos y estudiantes.
- **2026-06-09:** Fase 2: dependencia de certificado parcial, validacion de pagos academicos, bloqueo de solicitudes no elegibles y enlace solicitud-diploma-PDF.
