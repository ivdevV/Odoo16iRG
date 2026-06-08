# irg_elearning_editable_sections

## Descripción

`irg_elearning_editable_sections` extiende la edición de cursos de eLearning (`slide.channel` y `slide.slide`) para trabajar con secciones iRG editables y restricciones de contenidos por lotes (`allowed_batch_ids`).

## Corrección de edición por lotes y adjuntos grandes

### Incidente

Al limitar contenidos por lotes desde el apartado **Secciones iRG**, Odoo puede recalcular el formulario mediante `onchange` y construir snapshots de las líneas `slide.slide`. Si esas líneas incluyen campos binarios (`image_binary_content`, `binary_content`) asociados a adjuntos grandes, Odoo intenta leer `ir.attachment.datas` y serializar el contenido completo en base64.

En cursos con ficheros pesados, esa lectura puede agotar la memoria del worker y terminar en `MemoryError` antes de guardar el cambio de lotes.

### Solución

Los campos editables de contenidos y secciones se cargan ahora con `bin_size: True` en contexto:

- `slide_ids`
- `irg_native_section_ids`

Con este contexto, Odoo evita devolver el binario completo durante las lecturas generadas por el `onchange`; usa una representación ligera/tamaño del binario. Esto mantiene la edición de lotes sin forzar la carga de adjuntos pesados.

Los defaults existentes de creación se preservan, incluyendo `default_channel_id`, `default_is_category` y `default_slide_category`.

## Validación

La regresión se cubre con un test estático de vista:

```bash
python3 addons-extra/addons_uisep/irg_elearning_editable_sections/tests/test_slide_channel_view_bin_size.py
```

Resultado local: 2 tests ejecutados, 0 fallos, 0 errores.

También se validó junto con los módulos `irg_course_convocatorias` e `irg_course_convocatorias_v2` mediante:

```bash
python3 -m compileall -q \
  addons-extra/extrairg/irg_course_convocatorias_v2 \
  addons-extra/extrairg/irg_course_convocatorias \
  addons-extra/addons_uisep/irg_elearning_editable_sections
```

## Changelog

- **2026-06-05:** añadido `bin_size: True` a las relaciones editables de contenidos/secciones iRG para evitar `MemoryError` al limitar por lotes cuando existen adjuntos binarios grandes. Añadido test estático de regresión de la vista.
