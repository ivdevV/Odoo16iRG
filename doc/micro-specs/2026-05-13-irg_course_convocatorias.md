# irg_course_convocatorias

## 1. Título corto

Pestañas HomeClass y Online con convocatorias anuales en el formulario de curso eLearning.

## 2. Resumen objetivo

Añadir dos pestañas al formulario backend de `slide.channel` — **HomeClass** y **Online** — que permiten gestionar convocatorias anuales por modalidad, asociar lotes (`op.batch`) y organizar secciones de contenido específicas de cada convocatoria.

## 3. Motivo / justificación

Los cursos HomeClass se imparten en convocatorias anuales (identificadas por año, ej. HC2601) y el equipo académico necesita una forma de gestionar el contenido, los lotes y la variante de producto de cada convocatoria directamente desde la ficha del curso, sin mezclar información entre años. No se toca ningún módulo nativo ni de `addons_uisep`.

## 4. Alcance exacto

- Nuevo modelo `irg.course.convocatoria` (modelos Python).
- Herencia de `slide.channel` para añadir campos O2M de convocatorias HomeClass y Online.
- Herencia de `irg.slide.section` para añadir campo `convocatoria_id`.
- Vistas XML: form + list propio del nuevo modelo; inherit del form de `slide.channel`.
- `ir.model.access.csv` para el nuevo modelo.

## 5. Diseño técnico

**Nuevo modelo:** `irg.course.convocatoria`

| Campo | Tipo | Notas |
|---|---|---|
| `name` | Char | Requerido. Ej: "HomeClass 2026" |
| `modality` | Selection | `homeclass` / `online` |
| `year` | Char | "2026", "2025"… |
| `sequence` | Integer | Orden dentro del canal |
| `channel_id` | Many2one(`slide.channel`) | Requerido, ondelete=cascade |
| `batch_ids` | Many2many(`op.batch`) | Lotes asociados |
| `online_variant_id` | Many2one(`product.product`) | Solo para modalidad Online |
| `irg_section_ids` | One2many(`irg.slide.section`) | Secciones de esta convocatoria |

**Herencias Python:**
- `slide.channel` → añade `irg_homeclass_conv_ids` (domain `modality=homeclass`) e `irg_online_conv_ids` (domain `modality=online`).
- `irg.slide.section` → añade `convocatoria_id` Many2one(irg.course.convocatoria, ondelete='set null').

**Herencia XML:**
- `website_slides.view_slide_channel_form` vía XPath `//notebook/page[@name='irg_sections']` position=after.
- Dos `<page>` nuevas: "HomeClass" y "Online", cada una con un O2M tree + form popup que incluye pestaña de secciones.

## 6. Dependencias

```python
depends = ['website_slides', 'openeducat_core', 'irg_elearning_editable_sections']
```

## 7. Backwards-compatibility / migración

Sin impacto en datos existentes. El campo `convocatoria_id` en `irg.slide.section` es opcional (`set null`). Las secciones sin `convocatoria_id` siguen apareciendo en la pestaña "Secciones iRG" original.

## 8. Casos de prueba / criterios de aceptación

- El formulario de `slide.channel` muestra las pestañas "HomeClass" y "Online" tras instalar el módulo.
- Se puede crear una convocatoria "HomeClass 2026" desde la pestaña HomeClass; aparece como fila en el tree.
- Se pueden asignar lotes `op.batch` a la convocatoria.
- Desde la convocatoria se pueden crear secciones (`irg.slide.section`); dichas secciones aparecen también en la pestaña "Secciones iRG".
- En la pestaña Online, el campo `online_variant_id` es visible y seleccionable.
- Crear una convocatoria Online sin `online_variant_id` no bloquea el guardado (campo no required en v1).
- Las convocatorias HomeClass no aparecen en la pestaña Online y viceversa (domain funciona).
- Desinstalar el módulo no rompe el canal ni las secciones existentes.

## 9. Rollback plan

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> \
  -u website_slides,irg_elearning_editable_sections --stop-after-init \
  --db_host=pgodoo_latest
```

Desinstalar desde Apps > `irg_course_convocatorias`. Las columnas `irg_slide_section.convocatoria_id` y la tabla `irg_course_convocatoria` se eliminan al desinstalar.

## 10. Estimación y responsable

- Responsable: GitHub Copilot / iRG Dev
- Implementado: 2026-05-13
- Versión del módulo: `16.0.1.0.0`
