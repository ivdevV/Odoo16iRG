# irg_sign_reposition

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_sign_sale`, `isep_sign_sale_ext`, `irg_sale_order_extended`

---

## ¿Qué hace este módulo?

Proporciona lógica alternativa para el posicionamiento de `sign.template` y `sign.item` en el documento de prematrícula. A diferencia de `irg_sign_position_fix`, este módulo incluye un rediseño de la hoja de prematrícula y una reposición más completa de los elementos de firma.

## Funcionalidades principales

- Lógica alternativa de posicionamiento para `sign.template` y `sign.item`.
- Rediseño de la hoja de prematrícula.

## Vistas y UI

- `views/sheet_prematricula_restyle.xml` — diseño de la hoja de prematrícula.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_sign_reposition \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_sign_reposition \
    --stop-after-init --db_host=pgodoo_latest
```
