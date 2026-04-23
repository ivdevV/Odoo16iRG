# irg_subject_fix

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `isep_website_custom_design`, `isep_elearning_custom`, `isep_subject_precedence`, `website_slides`

---

## ¿Qué hace este módulo?

Corrige el filtrado de asignaturas por lote en el panel del alumno. El fix:

1. Respeta el campo `active` de `slide.channel.partner` (matrículas activas de eLearning).
2. Verifica las asignaturas precedentes antes de mostrar una asignatura como accesible.
3. Asegura que solo se muestren las asignaturas del lote activo del alumno.

## Funcionalidades principales

- Filtrado correcto de asignaturas por lote activo del alumno.
- Respeto de `active` en `slide.channel.partner`.
- Comprobación de precedencias de asignaturas.

## Vistas y UI

- `views/user_profile_content_details.xml` — vista corregida de asignaturas del panel del alumno.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_subject_fix \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_subject_fix \
    --stop-after-init --db_host=pgodoo_latest
```
