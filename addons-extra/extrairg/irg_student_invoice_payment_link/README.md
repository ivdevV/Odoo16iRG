# IRG Student Invoice Payment Link

Vincula facturas de cliente y pagos reconciliados con la ficha `op.student` aunque el titular contable de la factura sea un padre, empresa u otro tercero.

## Alcance

- Mantiene intactos `partner_id` y `partner_invoice_id` de la factura.
- Guarda el alumno academico en `account.move.irg_student_partner_id` desde `sale.order.student_id`.
- Rellena facturas existentes mediante hook de instalacion y migracion de actualizacion.
- Extiende el boton de facturas de `op.student` para incluir facturas donde el alumno figure como titular academico.
- Anade el smart button `Pagos`, resuelto desde los pagos reconciliados de las facturas academicas.

## Modelo de datos

- `account.move.irg_student_partner_id`: Many2one almacenado e indexado a `res.partner`, calculado desde las lineas de venta y propuesto desde `sale.order._prepare_invoice()`.
- `op.student.irg_invoice_count`: contador de facturas de cliente y rectificativas vinculadas al alumno por titular contable o alumno academico.
- `op.student.irg_payment_count`: contador de pagos reconciliados de las facturas academicas.

## Uso operativo

1. Crear una venta academica con `student_id` informado.
2. Mantener el pagador real en `partner_id` y `partner_invoice_id`.
3. Generar la factura desde la venta.
4. Consultar la ficha `op.student` para ver las facturas academicas y los pagos reconciliados desde los smart buttons.

## Facturas existentes

Al instalar el modulo, el `post_init_hook` rellena `irg_student_partner_id` en facturas de cliente y rectificativas ya creadas que tengan lineas procedentes de pedidos con `student_id`.

Si el modulo ya estaba instalado, actualizar a la version `16.0.1.1.0` ejecuta la migracion:

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d <db> -u irg_student_invoice_payment_link \
  --stop-after-init
```

Tambien puede forzarse desde shell si fuera necesario:

```python
env['account.move'].irg_backfill_student_partner_id()
```

## Validacion

Ejecutar en Odoo local:

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d <db> -i irg_student_invoice_payment_link \
  --test-enable --test-tags /irg_student_invoice_payment_link \
  --without-demo=all --max-cron-threads=0 \
  --stop-after-init --log-level=test
```

Validacion documentada:

- Compilacion Python correcta.
- XML correcto.
- Instalacion local correcta con `odoo_local`.
- Tests del modulo: 4 ejecutados, 0 fallos, 0 errores.

## Limitaciones conocidas

- Si una factura agrupa lineas de pedidos de varios alumnos, solo se guarda el primer alumno encontrado.
- El smart button `Pagos` muestra pagos solo cuando estan reconciliados con las facturas academicas.

## Changelog

- **2026-06-09:** Creacion del modulo con vinculo academico factura-alumno, smart buttons de facturas/pagos y tests transaccionales.
- **2026-06-09:** Anade backfill para facturas existentes mediante `post_init_hook`, migracion y metodo manual.
