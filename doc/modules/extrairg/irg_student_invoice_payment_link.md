# irg_student_invoice_payment_link

## Ficha Tecnica

| Propiedad | Valor |
| --- | --- |
| Nombre tecnico | `irg_student_invoice_payment_link` |
| Version | `16.0.1.1.0` |
| Categoria | Education |
| Licencia | LGPL-3 |
| Autor | iRG |
| Tipo | Modulo de herencia |

## Dependencias

- `account`
- `sale`
- `openeducat_fees`
- `irg_sale_order_extended`

## Proposito

Permite que la ficha `op.student` vea facturas y pagos academicos aunque el titular contable de la factura sea un padre, empresa u otro tercero. El modulo usa `sale.order.student_id` como vinculo academico y no modifica `partner_id` ni `partner_invoice_id`.

## Cambios En Modelos

### `account.move`

- `irg_student_partner_id`: Many2one almacenado e indexado a `res.partner`. Se calcula desde `invoice_line_ids.sale_line_ids.order_id.student_id` y tambien se propone desde `sale.order._prepare_invoice()` al crear facturas desde ventas.
- `irg_backfill_student_partner_id()`: metodo de mantenimiento que rellena el alumno academico en facturas existentes creadas desde pedidos con `student_id`.

### `sale.order`

- `_prepare_invoice()`: copia `student_id` a `irg_student_partner_id` en los valores de factura cuando existe alumno academico.

### `op.student`

- `irg_invoice_count`: contador de facturas academicas.
- `irg_payment_count`: contador de pagos reconciliados de esas facturas.
- `action_view_invoice()`: muestra facturas de cliente y rectificativas donde `partner_id` sea el alumno o `irg_student_partner_id` sea el alumno.
- `action_view_academic_payments()`: abre pagos obtenidos con `_get_reconciled_payments()` desde las facturas academicas vinculadas.

## Cambios En Vistas

- La factura de cliente muestra `irg_student_partner_id` despues de `partner_id` y solo para facturas/rectificativas de cliente.
- La ficha `op.student` reutiliza el smart button de facturas de `openeducat_fees` para mostrar el nuevo contador academico.
- La ficha `op.student` anade el smart button `Pagos` junto al boton de facturas.

## Uso Operativo

- Crear una venta academica con `student_id` informado y con el pagador real en `partner_id`/`partner_invoice_id`.
- Generar la factura desde la venta; el modulo copia el alumno a `irg_student_partner_id` sin cambiar el titular contable.
- Abrir la ficha `op.student` del alumno para consultar el smart button de facturas academicas.
- Usar el smart button `Pagos` para revisar pagos reconciliados con esas facturas.

## Datos Existentes

El modulo cubre facturas anteriores mediante dos mecanismos:

- `post_init_hook`: se ejecuta al instalar el modulo por primera vez y rellena `irg_student_partner_id` en facturas de cliente/rectificativas con lineas de venta enlazadas a pedidos que tengan `student_id`.
- Migracion `16.0.1.1.0`: se ejecuta al actualizar el modulo si ya estaba instalado previamente.

Comando recomendado para actualizar una base existente:

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d <db> -u irg_student_invoice_payment_link \
  --stop-after-init
```

Si se necesita forzar manualmente desde shell:

```python
env['account.move'].irg_backfill_student_partner_id()
```

## Decisiones De Diseno

- Se crea un modulo nuevo por herencia para cumplir la regla de no modificar modulos existentes.
- El titular contable de factura permanece intacto para no alterar contabilidad, impuestos ni cobros.
- El campo de alumno academico es almacenado para permitir busquedas, dominios y filtros eficientes.
- Los pagos se resuelven desde facturas reconciliadas mediante `_get_reconciled_payments()`, evitando enlaces manuales fragiles entre alumno y pagos.
- No se crean modelos nuevos, por lo que no se anaden ACLs propias.

## Validacion Realizada

Comandos ejecutados:

```bash
python3 -m compileall addons-extra/extrairg/irg_student_invoice_payment_link
```

```bash
python3 -c "import pathlib, xml.etree.ElementTree as ET; [ET.parse(str(p)) for p in pathlib.Path('addons-extra/extrairg/irg_student_invoice_payment_link').glob('views/*.xml')]; print('XML OK')"
```

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d irg_student_invoice_payment_link_test3 \
  -i irg_student_invoice_payment_link \
  --test-enable --test-tags /irg_student_invoice_payment_link \
  --without-demo=all --max-cron-threads=0 \
  --stop-after-init --log-level=test
```

Resultado:

- Compilacion Python correcta.
- XML correcto.
- Instalacion del modulo correcta.
- Tests del modulo: 4 ejecutados, 0 fallos, 0 errores.

## Limitaciones Conocidas

- Si una factura agrega lineas de pedidos de varios alumnos, `irg_student_partner_id` guarda el primer alumno encontrado porque el campo es Many2one.
- El smart button `Pagos` muestra pagos solo cuando estan reconciliados con las facturas academicas.

## Changelog

- **2026-06-09:** Creacion del modulo con vinculo academico factura-alumno, acciones de facturas/pagos en `op.student`, vistas heredadas y tests transaccionales.
- **2026-06-09:** Version `16.0.1.1.0`: backfill de facturas existentes via `post_init_hook`, migracion de actualizacion y metodo manual.
