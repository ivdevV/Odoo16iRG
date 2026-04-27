# irg_elearning_styles_rework

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `website_slides`, `website`, `openeducat_lms`, `openeducat_lms_website`, `isep_website_custom`

---

## ¿Qué hace este módulo?

Rework visual moderno para todas las páginas del eLearning (campus virtual). Reemplaza el diseño predeterminado de OpenEduCat LMS con un aspecto más moderno y alineado con la identidad visual de IRG/ISEP, mejorando la experiencia del alumno en la plataforma de aprendizaje.

## Funcionalidades principales

- Override de vistas del eLearning para diseño moderno.
- SCSS completo para el rework visual.
- Reglas de seguridad específicas para el eLearning renovado.

## Vistas y UI

- `views/website_slides_rework.xml` — override de templates del eLearning.
- SCSS: `irg_elearning_styles_rework/static/src/scss/irg_elearning_styles_rework.scss`.

## Notas técnicas

- Requiere `security/ir.model.access.csv`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_elearning_styles_rework \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_elearning_styles_rework \
    --stop-after-init --db_host=pgodoo_latest
```
