# isep_website_custom_design

**Categoría:** addons_uisep
**Versión:** 16.2
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `isep_website_custom`, `website_profile`, `isep_openeducat_custom`

---

## ¿Qué hace este módulo?

Capa de diseño visual del campus de ISEP. Extiende `isep_website_custom` con el diseño específico: estilos SCSS, overrides de templates para la identidad visual de ISEP, adaptaciones de la página de perfil de eLearning y diseño de las tarjetas de curso.

## Funcionalidades principales

- SCSS de diseño del campus ISEP.
- Overrides de templates de perfil de usuario de eLearning.
- Diseño de tarjetas de curso en el campus.
- Adaptaciones visuales de la página de perfil.

## Vistas y UI

- Override de templates del campus con identidad visual ISEP.
- SCSS en `web.assets_frontend`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_website_custom_design \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_website_custom_design \
    --stop-after-init --db_host=pgodoo_latest
```
