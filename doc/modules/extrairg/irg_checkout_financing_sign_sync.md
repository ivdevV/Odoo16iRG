# irg_checkout_financing_sign_sync

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `irg_sale_subscription_esp`, `isep_website_sale_custom`, `irg_migration_fields`, `base_vat_optional_vies`

---

## ¿Qué hace este módulo?

Sincroniza la información de financiación en el checkout y los datos de matrícula necesarios para la firma electrónica. Es el módulo que conecta el flujo del carrito de compra con el proceso de firma del contrato de matrícula, asegurando que todos los campos relevantes se trasladen correctamente.

## Funcionalidades principales

- Sincronización de datos de financiación entre checkout y documentos de firma.
- Formulario de campos de matrícula post-pago para subida de documentos.
- Fix del resumen del carrito con datos de financiación correctos.
- Movimiento de campos de dirección en el formulario de checkout.
- Fix de campos de información extra en el proceso de compra.
- Vista de adjuntos académicos en el pedido de venta.
- Fix del informe de registro (prematrícula).

## Vistas y UI

- `views/cart_summary_fix.xml`, `views/address_fields_move.xml`, `views/extra_info_fields_fix.xml`.
- `views/post_payment_upload.xml` — formulario de subida post-pago.
- `views/registration_report_fix.xml`, `views/sale_order_academic_attachments.xml`.

## Integración y Consistencia de Financiación (Presupuestos Manuales Backend)

Con el fin de garantizar la consistencia en el cálculo de gastos de financiación en presupuestos manuales creados o editados directamente desde el backend (Odoo), se ha incorporado un mecanismo de cálculo automático e idempotente de las líneas de financiación.

### Automatización mediante Hooks (create y write)
El módulo intercepta la creación y modificación de presupuestos de venta (`sale.order`) a través de la sobrescritura de los métodos `create` (con soporte multi-registro `@api.model_create_multi`) y `write`. 

- **Estados aplicables:** El cálculo consistente de la financiación solo se ejecuta para pedidos que se encuentren en estados de borrador (`draft`) o presupuesto enviado (`sent`).
- **Desencadenadores:** La consistencia se evalúa de manera automática al modificar los siguientes campos clave en el presupuesto:
  - Líneas de pedido (`order_line`)
  - Tarifa (`pricelist_id`)
  - Plazos de pago (`payment_term_id`)
  - Número de plazos (`term_number`)
- **Evitación de recursión:** Para prevenir bucles infinitos durante el guardado de datos, se utiliza el flag de contexto `skip_financing_recompute`.

### Botón "Recalcular Financiación"
Para dar flexibilidad al comercial y permitir actualizaciones manuales inmediatas sobre la cotización, se ha añadido el botón **"Recalcular Financiación"** en la cabecera (`header`) de la vista de formulario de presupuestos (definida en `views/sale_order_academic_attachments.xml`).
- **Visibilidad:** El botón es visible exclusivamente para presupuestos en estados `draft` o `sent`.
- **Acción técnica:** Invoca el método backend `action_recalculate_financing()`, el cual fuerza la recalculación e idempotencia de la financiación del presupuesto actual.

### Flujo de Limpieza e Idempotencia
El proceso de consistencia implementado asegura que no se acumulen líneas erróneas ni se altere el estado original si el cliente opta por no financiar:
- **Limpieza de huérfanos:** Se eliminan de forma automática todas las líneas de financiación obsoletas que ya no se correspondan con el plan o plazos de pago actualmente seleccionados.
- **Transición a Pago al Contado:** Si el plan de pagos del pedido se cambia a una modalidad de contado (no financiada):
  - Se eliminan todas las líneas de gastos de financiación remanentes.
  - Se restaura el precio unitario original del producto/servicio si este fue previamente modificado por la tarifa de financiación.
  - Se limpian los campos internos de control: `irg_line_type`, `irg_force_price_unit_set` e `irg_force_price_unit`.

### Pruebas y Validación
Para garantizar la fiabilidad del sistema de persistencia y consistencia, se han diseñado y ejecutado con éxito tests unitarios automáticos en el entorno de desarrollo local con Docker (usando `docker-compose.local.yml`). Estas pruebas cubren:
- Casos de creación e inserción automática de líneas de financiación.
- Actualización dinámica al modificar líneas y tarifas.
- Transición limpia a pago al contado y restauración de precios unitarios.
- Prevención de recursión y bucles infinitos en operaciones de escritura complejas.

## Changelog
### Versión 16.0.1.1.0
- **Feature:** Automatización e integración de gastos de financiación en presupuestos manuales del backend (hooks en `create` y `write`).
- **Feature:** Añadido botón "Recalcular Financiación" en el formulario del backend para permitir cálculos manuales bajo demanda por parte del comercial.
- **Fix/Refactor:** Control de idempotencia con limpieza de líneas de financiación huérfanas y restauración de tarifa original al pasar a contado.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_checkout_financing_sign_sync \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_checkout_financing_sign_sync \
    --stop-after-init --db_host=pgodoo_latest
```
