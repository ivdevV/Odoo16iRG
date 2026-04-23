# irg_timetable_subject_prefix

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `openeducat_timetable_enterprise`, `isep_openeducat_custom`, `isep_time_link_url`

---

## ¿Qué hace este módulo?

Muestra el código de la asignatura como prefijo en el título de cada evento del calendario portal. Por ejemplo, en lugar de ver solo "Matemáticas", el alumno verá "MAT001 — Matemáticas", facilitando la identificación de asignaturas cuando hay nombres similares.

## Funcionalidades principales

- Computed field o override que añade el código de asignatura al título del evento.
- Compatible con la visualización del calendario en el portal del alumno.

## Vistas y UI

Sin vistas propias visibles; la modificación se aplica en el rendering del título del evento del calendario.

## Notas técnicas

- Requiere `security/ir.model.access.csv`.
- Es dependencia de `irg_timetable_session_title_endpoint`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_timetable_subject_prefix \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_timetable_subject_prefix \
    --stop-after-init --db_host=pgodoo_latest
```
