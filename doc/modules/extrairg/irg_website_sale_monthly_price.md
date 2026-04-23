# irg_website_sale_monthly_price

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `website_sale`, `product`, `irg_website_sale_custom`, `website_sale_subscription`

---

## ¿Qué hace este módulo?

Muestra el precio mensual equivalente de los productos de suscripción en el catálogo y páginas de producto de la tienda online (versión IRG). Permite a los visitantes ver cuánto pagarán al mes por un programa educativo sin necesidad de añadirlo al carrito primero.

## Funcionalidades principales

- Override del template de precio del producto para mostrar precio mensual.
- Script JavaScript para gestión de visibilidad de formularios de precio.
- CSS para control de visibilidad de elementos de precio.

## Vistas y UI

- `views/product_price_template.xml` — template de precio mensual.
- JS: `irg_website_sale_monthly_price/static/src/js/website_sale_monthly.js`.
- CSS: `irg_website_sale_monthly_price/static/src/css/form-visibility.css`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_website_sale_monthly_price \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_website_sale_monthly_price \
    --stop-after-init --db_host=pgodoo_latest
```
