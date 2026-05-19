# irg_course_convocatorias

## 1. Título corto

Pestañas HomeClass y Online con convocatorias anuales en el formulario de curso eLearning.

## 2. Resumen objetivo

Reestructurar el formulario backend de `slide.channel` para que las modalidades **HomeClass** y **Online** aparezcan como pestañas superiores, y que cada una contenga su propio notebook interno con subpestañas del tipo `Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas` y `Secciones iRG`.

## 3. Motivo / justificación

La primera aproximación basada en un modelo manual `irg.course.convocatoria` no seguía el flujo real del proyecto. El patrón correcto ya existe en `irg_op_course_modality`: las modalidades viven en `op.course` mediante catálogo, y los lotes reales viven en `op.batch`. Este módulo debe apoyarse en esa base para que la UI de `slide.channel` refleje modalidades, lotes y contenido reales del curso.

## 4. Alcance exacto

- Herencia de `slide.channel` para añadir campos calculados de cursos relacionados, modalidades, lotes HomeClass, lotes Online, variante Online y secciones filtradas para ambas modalidades.
- Reestructuración del notebook principal del formulario para introducir un notebook superior por modalidad.
- Reutilización de las pestañas existentes del canal dentro de HomeClass y definición de un notebook paralelo para Online.
- Dependencia explícita de `irg_op_course_modality` e `isep_elearning_custom`.

## 5. Diseño técnico

**Herencias Python:**
- `slide.channel` → añade campos calculados:
  - `irg_related_course_ids`
  - `irg_related_modality_ids`
  - `irg_homeclass_batch_ids`
  - `irg_online_batch_ids`
  - `irg_homeclass_section_ids`
  - `irg_online_variant_id`
  - `irg_has_homeclass`
  - `irg_has_online`
- La relación `slide.channel` → `op.course` se obtiene por dos vías:
  - asignaturas del canal (`op_subject_ids.course_id` y `subject_ids`)
  - cursos que incluyen el canal en `slide_channel_ids`
- Los lotes HomeClass/Online se calculan desde `op.batch` de los cursos relacionados y `modality_id`.
- La variante Online se obtiene de `course.product_id.product_tmpl_id.product_variant_ids` filtrando por atributo `modalidad = online`.
- Las secciones HomeClass se calculan sobre `irg_native_section_ids` filtrando `allowed_batch_ids` contra los lotes HomeClass.

**Herencia XML:**
- `website_slides.view_slide_channel_form` vía inserción de un notebook superior nuevo antes del notebook base.
- Pestaña superior **HomeClass**: contiene un notebook interno al que se mueven las pestañas existentes del canal (`content`, `description`, `options`, `karma_rules`, `op_subject`, `irg_sections`).
- Pestaña superior **Online**: contiene un notebook interno propio con `Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas` y `Secciones iRG` construidas sobre datos online.
- En `Online > Contenido`, se muestran contenidos nativos `slide.slide` marcados como Online.
- La subpestaña `Online > Contenido` usa el campo técnico `irg_online_slide_ids`, un `one2many` contra `slide.slide/channel_id` con dominio por modalidad para evitar duplicar `slide_ids` en el mismo formulario.
- La separación editable del contenido se implementa en `slide.slide` mediante `irg_content_modality`, evitando modelos paralelos y permitiendo añadir secciones, documentos y demás contenidos desde Online sin mezclarlos con HomeClass.
- El botón `Copiar contenido de HomeClass` clona contenidos y secciones como registros independientes de Online, preserva el orden visual del bloque copiado y reasigna la jerarquía (`category_id`, `parent_slide_id` y sección iRG) a las copias nuevas para evitar vínculos cruzados.
- El notebook original del formulario se oculta tras mover las pestañas reutilizadas a HomeClass.

## 6. Dependencias

```python
depends = ['website_slides', 'openeducat_core', 'irg_op_course_modality', 'isep_elearning_custom', 'irg_elearning_editable_sections']
```

## 7. Backwards-compatibility / migración

Sin impacto destructivo en datos existentes. La UI del canal pasa a reflejar cursos, modalidades y lotes reales; no se requiere migración de datos para visualizar la nueva estructura.

## 8. Casos de prueba / criterios de aceptación

- El formulario de `slide.channel` muestra las pestañas "HomeClass" y "Online" tras instalar el módulo.
- Si el curso relacionado tiene modalidad HomeClass o lotes HomeClass, la pestaña HomeClass es visible.
- Si el curso relacionado tiene modalidad Online o lotes Online, la pestaña Online es visible.
- El formulario de `slide.channel` muestra primero las pestañas superiores `HomeClass` y `Online`.
- Al entrar en HomeClass, aparecen dentro las subpestañas del canal (`Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas`, `Secciones iRG`).
- Al entrar en Online, aparecen subpestañas equivalentes adaptadas a datos online.
- La pestaña Online muestra lotes `op.batch` reales filtrados por modalidad Online y la variante Online detectada.
- La pestaña `Online > Contenido` permite crear contenidos nativos `slide.slide` marcados como Online.
- La pestaña `Online > Contenido` permite crear secciones nativas marcadas como Online mediante el botón `Añadir sección`.
- El botón `Copiar contenido de HomeClass` copia secciones y documentos a Online como registros independientes, sin dejar documentos online vinculados a secciones HomeClass.
- La copia no debe añadir secciones Online a la lista de secciones HomeClass ni alterar el orden visible de HomeClass.
- Los contenidos copiados a Online deben conservar los datos propios de una copia normal, sin modificar ni reordenar los registros HomeClass originales.
- Las pestañas de modalidad no muestran ya el diseño plano previo a nivel superior.

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
- Versión del módulo: `16.0.1.2.0`
