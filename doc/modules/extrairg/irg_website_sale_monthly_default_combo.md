# irg_website_sale_monthly_default_combo

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `isep_website_sale_monthly_price`, `isep_website_sale_custom`, `website_sale`

---

## ¿Qué hace este módulo?

Alinea el precio mensual mostrado en el listado de la tienda con la combinación predeterminada del producto. Corrige el caso en el que el precio mensual del listado no coincidía con el precio real al seleccionar las opciones predeterminadas del producto.

## Funcionalidades principales

- Override del template de precio para usar la combinación predeterminada del producto.
- Script JavaScript para cargar la combinación online predeterminada.

## Vistas y UI

- `views/product_price_template.xml` — template de precio con combinación predeterminada.
- JS: `static/src/js/default_online_combo.js`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_website_sale_monthly_default_combo \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_website_sale_monthly_default_combo \
    --stop-after-init --db_host=pgodoo_latest
```
