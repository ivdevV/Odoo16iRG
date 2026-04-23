# irg_website_checkout_fixes

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** Instituto Raimon Gaju
**Depende de:** `website_sale`

---

## ¿Qué hace este módulo?

Corrige varios problemas visuales y de UX en la página de checkout (`/shop/address`):
- Rellena los valores de cuotas que aparecían vacíos (`{}` → número real).
- Cambia la etiqueta "Nombre de quíen factura" por "Nombre en la Factura".
- Mejora el contraste de los campos de entrada (fondo blanco).

Ver: `doc/micro-specs/2026-03-16-irg_website_checkout_fixes.md`.

## Funcionalidades principales

- Fix de cuotas vacías en el resumen de checkout.
- Corrección de etiqueta del campo de nombre de factura.
- CSS que mejora el contraste de inputs en el checkout.

## Vistas y UI

- `views/website_templates.xml` — override de templates del checkout.
- CSS: `irg_website_checkout_fixes/static/src/css/checkout_fix.css`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_website_checkout_fixes \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_website_checkout_fixes \
    --stop-after-init --db_host=pgodoo_latest
```
