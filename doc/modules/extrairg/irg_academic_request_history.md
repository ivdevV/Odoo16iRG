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
- `openeducat_core`

## Proposito

Este modulo prepara la Fase 1 del flujo de solicitudes academicas del portal. Extiende `irg.certificate.request` para convertirlo en el registro unico de historial y trazabilidad de certificados y diplomas solicitados por alumnos.

No cambia todavia el flujo de pago del portal. Los pagos por Stripe Checkout Session, webhooks y paginas post-pago se implementaran en fases posteriores.

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
- Pestana `Pago Stripe` con resumen de pago y evidencias Stripe.
- Columnas opcionales en lista para estudiante, fecha de pago y estado Stripe.
- Busqueda por estudiante, Stripe Session y PaymentIntent.
- Filtro `Pagado Stripe` y agrupacion por estudiante.

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

## Limitaciones Conocidas

- Los campos Stripe se preparan pero no se rellenan todavia.
- `diploma_registry_id` se prepara pero se vinculara cuando se implemente la fase de generacion post-pago.
- El portal sigue usando el flujo de pago existente hasta las fases de Stripe Checkout.

## Changelog

- **2026-06-09:** Creacion del modulo de Fase 1 con trazabilidad de solicitudes academicas, campos de evidencia Stripe y smart buttons en contacto/estudiante.
- **2026-06-09:** Ajuste de visibilidad para mostrar siempre el smart button `Solicitudes` en contactos y estudiantes.
