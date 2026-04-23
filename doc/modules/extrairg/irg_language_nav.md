# irg_language_nav

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `website`

---

## ¿Qué hace este módulo?

Añade un selector de idioma en la barra superior del sitio web que coloca los idiomas Español (ES) e Inglés (EN) primero, seguidos del resto en orden alfabético. Proporciona una experiencia de cambio de idioma más intuitiva para el público español.

La plantilla `irg_language_nav.irg_language_selector` es referenciada externamente por `theme_silon/header.xml`.

## Funcionalidades principales

- Selector de idioma en la barra superior del sitio web.
- ES e EN se muestran siempre primero.
- El resto de idiomas en orden alfabético.

## Vistas y UI

- `views/language_nav.xml` — plantilla del selector de idioma.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_language_nav \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_language_nav \
    --stop-after-init --db_host=pgodoo_latest
```
