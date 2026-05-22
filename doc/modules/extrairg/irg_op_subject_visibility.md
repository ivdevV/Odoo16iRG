# irg_op_subject_visibility

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG Developer
**Depende de:** `openeducat_core`, `openeducat_teams`, `irg_op_subject_multi_course`, `isep_elearning_custom`, `isep_website_custom`, `irg_subject_fix`

---

## ¿Qué hace este módulo?

Extiende `op.subject` con campos de visibilidad por lote/promoción. Permite definir si una asignatura es visible para todos los lotes del curso o solo para lotes específicos. Además, restringe el acceso a los canales de eLearning (`slide.channel`) en función del lote activo del alumno.

## Funcionalidades principales

- Campo `visible_all_course_batches` — visibilidad global o por lote.
- Campo `batch_visibility_ids` — lotes para los que la asignatura es visible.
- Campo computado `effective_batch_ids` — lotes efectivos considerando la visibilidad.
- Restricción del acceso a `slide.channel` según el lote activo del alumno.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.subject` | Herencia | `visible_all_course_batches`, `batch_visibility_ids`, `effective_batch_ids` |
| `slide.channel` | Herencia | Restricción de acceso por lote |

## Vistas y UI

- `views/op_subject_visibility_views.xml` — campos de visibilidad en el formulario de asignatura.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_op_subject_visibility \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_op_subject_visibility \
    --stop-after-init --db_host=pgodoo_latest
```

## Changelog

### [16.0.1.1.0] - 2026-05-22
- Modificación del método `get_subjects_visible_for_batch(batch, admission=None)` en `op.course` para soportar el contexto de apertura de asignaturas online.
- Filtro en portal ajustado en `portal_subject_visibility.xml` para pasar la variable `vis_admission` de admisión al método de visibilidad de asignaturas.
