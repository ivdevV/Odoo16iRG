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
