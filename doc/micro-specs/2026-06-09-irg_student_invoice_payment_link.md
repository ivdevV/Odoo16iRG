# Micro-spec: irg_student_invoice_payment_link

## Contexto

En ventas academicas puede ocurrir que el titular contable de la factura sea un padre, empresa u otro tercero, mientras `sale.order.student_id` apunta al partner del alumno. OpenEduCat muestra actualmente facturas desde `student.invoice_ids`, por lo que la ficha `op.student` no ve esas facturas cuando `partner_id` no es el alumno.

## Alcance

- Crear un modulo nuevo en `addons-extra/extrairg/` por herencia.
- Anadir en `account.move` un campo almacenado `irg_student_partner_id` para el alumno academico.
- Poblar el campo desde ventas sin modificar el titular contable de factura.
- Rellenar facturas existentes desde lineas de venta vinculadas a pedidos con `student_id`.
- Ampliar `op.student.action_view_invoice()` para listar facturas de cliente y rectificativas donde el alumno sea titular contable o alumno academico.
- Anadir conteo y accion de pagos academicos desde pagos reconciliados de esas facturas.
- Mostrar el alumno academico discretamente en la factura y un smart button `Pagos` en la ficha de estudiante.

## Fuera de alcance

- Cambiar `partner_id`, `partner_invoice_id` o reglas contables de facturacion.
- Crear modelos nuevos, ACLs o reglas de seguridad nuevas.
- Relacionar pagos no reconciliados con facturas.
- Inferir alumnos en facturas que no procedan de pedidos de venta o cuyas lineas no conserven `sale_line_ids`.
- Modificar directamente modulos existentes.

## Validacion esperada

- El modulo instala correctamente en Odoo 16 local.
- Una factura generada desde una venta con pagador tercero conserva el pagador en `partner_id`.
- La factura guarda `irg_student_partner_id` con el partner del alumno.
- Las facturas existentes creadas desde ventas se pueden rellenar con el backfill del modulo.
- La accion de facturas de `op.student` incluye esa factura.
- La accion de pagos usa los pagos reconciliados de las facturas academicas.

## Validacion realizada

Comando local usado con el servicio `odoo_local`:

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d irg_student_invoice_payment_link_test3 \
  -i irg_student_invoice_payment_link \
  --test-enable --test-tags /irg_student_invoice_payment_link \
  --without-demo=all --max-cron-threads=0 \
  --stop-after-init --log-level=test
```

Resultado documentado: instalacion correcta del modulo y 4 tests ejecutados sin fallos ni errores.

## Limitaciones conocidas

- Si una factura agrupa lineas de pedidos de varios alumnos, solo se guarda el primer alumno encontrado en `irg_student_partner_id`.
- Los pagos solo aparecen si estan reconciliados con las facturas academicas.

## Changelog

- **2026-06-09:** Definido e implementado el modulo de vinculo academico factura-alumno con acciones de facturas y pagos en `op.student`.
- **2026-06-09:** Anade backfill de facturas existentes para bases instaladas o actualizadas.
