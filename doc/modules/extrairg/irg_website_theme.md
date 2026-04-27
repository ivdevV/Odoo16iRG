# irg_website_theme

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `website`, `isep_website_custom`, `web`

---

## ¿Qué hace este módulo?

Es el módulo de tema visual centralizado para el sitio web Odoo 16 de IRG/ISEP. Centraliza toda la identidad visual de la instancia en un único punto: paleta de colores corporativa, tipografía, overrides de navbar y footer, y estilos de componentes.

Al cargarse con `prepend` en el bundle de assets, sus variables Bootstrap (`$primary`, `$secondary`, etc.) se compilan **antes** que el resto de estilos, garantizando que todos los módulos que consumen variables Bootstrap hereden la identidad visual corporativa.

## Funcionalidades principales

- Variables Bootstrap corporativas (colores primario/secundario, fuentes) vía SCSS `prepend`.
- Tipografía corporativa Inter (Google Fonts) inyectada en el `<head>` de todas las páginas.
- Overrides de navbar y footer vía XPath en `views/layout_overrides.xml`.
- Estilos de cards, botones, badges, inputs, tablas, breadcrumbs y portal del alumno.
- Carga garantizada como primer SCSS del bundle para propagación de variables.

## Vistas y UI

- `views/layout_overrides.xml` — overrides de layout, navbar y footer.
- SCSS prepend: `irg_website_theme/static/src/scss/irg_theme.scss`.

## Dependencias externas

- `isep_website_custom` — campus y portal base sobre el que aplica el tema.

## Notas técnicas

- Usa `('prepend', ...)` en `web.assets_frontend` para garantizar el orden de compilación SCSS.
- Ver micro-spec: `doc/micro-specs/2026-04-23-irg_website_theme.md`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_website_theme \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_website_theme \
    --stop-after-init --db_host=pgodoo_latest
```
