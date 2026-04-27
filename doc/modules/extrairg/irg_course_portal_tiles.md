# irg_course_portal_tiles

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `isep_website_custom`, `openeducat_web`, `website_helpdesk`

---

## ¿Qué hace este módulo?

Añade tarjetas de acceso rápido (tiles) en el panel del campus por cada curso del alumno: enlace al calendario, a prácticas, al TFM/TFG y a la página de ayuda (helpdesk). También incluye overrides de etiquetas del perfil de OpenEduCat y una página de fallback para el TFM.

## Funcionalidades principales

- Tiles de acceso rápido: Calendario, Prácticas, TFM, Ayuda.
- Override de etiquetas en el perfil de usuario de OpenEduCat.
- Página de fallback para el enlace TFM cuando no está configurado.
- Overrides de la página de helpdesk.
- Chatbot de ayuda (JS) y parche del menú de campus.

## Vistas y UI

- `views/irg_course_portal_tiles_views.xml` — tiles de acceso rápido.
- `views/user_profile_openeducat_label_override.xml` — etiquetas.
- `views/tfm_views.xml`, `views/tfm_page_fallback.xml` — TFM.
- `views/helpdesk_page.xml`, `views/helpdesk_overrides.xml` — helpdesk.

## Notas técnicas

- JS: `help_chatbot.js` (chatbot de ayuda) y `menu_patch.js` (parche de menú).
- SCSS: `irg_tiles.scss`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_course_portal_tiles \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_course_portal_tiles \
    --stop-after-init --db_host=pgodoo_latest
```
