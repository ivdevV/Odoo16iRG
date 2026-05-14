# irg_course_convocatorias

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `website_slides`, `openeducat_core`, `irg_op_course_modality`, `isep_elearning_custom`, `irg_elearning_editable_sections`

---

## ¿Qué hace este módulo?

Añade una capa de lectura académica sobre los cursos de eLearning (`slide.channel`) para separar visualmente la información HomeClass y Online usando la estructura real del proyecto. En lugar de crear convocatorias manuales desde el canal, el módulo parte de los cursos `op.course` relacionados, sus modalidades (`irg_op_course_modality`) y sus lotes reales (`op.batch`), y reorganiza el formulario en dos niveles de pestañas.

Las pestañas superiores **HomeClass** y **Online** aparecen por encima de las pestañas funcionales del canal. Dentro de **HomeClass** se reutiliza el notebook real del curso (`Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas`, `Secciones iRG`). Dentro de **Online** se construye un notebook paralelo orientado a lotes, variante y secciones online.

En la práctica, el módulo actúa como puente entre la estructura nativa de `website_slides`, la organización académica de OpenEduCat y el modelo de secciones editables aportado por `irg_elearning_editable_sections`. No expone controladores ni lógica de portal; su impacto es principalmente de backoffice y de modelado de datos para el equipo académico.

## Funcionalidades principales

- Calcula automáticamente los cursos `op.course` relacionados con el `slide.channel`.
- Lee las modalidades disponibles desde `irg_op_course_modality` en `op.course.irg_modality_ids`.
- Calcula los lotes HomeClass y Online reales a partir de `op.batch.course_id` y `op.batch.modality_id`.
- Calcula la variante Online desde el producto del curso cuando existe una variante con atributo `modalidad = online`.
- Filtra las secciones HomeClass y Online sobre las secciones nativas del canal usando `allowed_batch_ids`.
- Filtra `Online > Contenido` sobre `slide.slide`, mostrando contenidos marcados con modalidad Online.
- Renderiza `Online > Contenido` usando `irg_online_slide_ids`, un `one2many` técnico contra `slide.slide/channel_id`, para mantener contenidos editables sin duplicar `slide_ids` en el mismo formulario.
- Añade `irg_content_modality` a `slide.slide` para que HomeClass y Online puedan tener contenidos nativos separados dentro del mismo canal.
- Permite crear secciones desde `Online > Contenido` con los mismos defaults estructurales que HomeClass y con modalidad Online.
- Oculta las pestañas HomeClass/Online cuando no hay modalidad ni lotes aplicables.
- Reordena la UX del formulario para que HomeClass y Online sean las pestañas de primer nivel y el resto queden como subpestañas internas.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.course.convocatoria` | Nuevo/auxiliar | `name`, `modality`, `year`, `sequence`, `active`, `channel_id`, `batch_ids`, `online_variant_id`, `irg_section_ids`, `section_count` |
| `slide.channel` | Herencia | `irg_related_course_ids`, `irg_related_modality_ids`, `irg_homeclass_batch_ids`, `irg_online_batch_ids`, `irg_homeclass_section_ids`, `irg_online_content_ids`, `irg_online_slide_ids`, `irg_online_section_ids`, `irg_online_variant_id`, `irg_has_homeclass`, `irg_has_online` |
| `slide.slide` | Herencia | `irg_content_modality` |
| `irg.slide.section` | Herencia | `convocatoria_id` |

### Detalle funcional de campos

- `irg_related_course_ids`: cursos relacionados con el canal por asignaturas o por `slide_channel_ids`.
- `irg_related_modality_ids`: modalidades del catálogo `irg.course.modality` presentes en los cursos relacionados.
- `irg_homeclass_batch_ids`: lotes reales del curso filtrados como HomeClass.
- `irg_online_batch_ids`: lotes reales del curso filtrados como Online.
- `irg_homeclass_section_ids`: secciones nativas del canal cuyo `allowed_batch_ids` intersecta con los lotes HomeClass.
- `irg_online_content_ids`: contenidos del canal visibles para online según `irg_content_modality`.
- `irg_online_slide_ids`: relación editable a `slide.slide` filtrada por modalidad Online, usada por la pestaña `Online > Contenido`.
- `irg_content_modality`: marca en cada contenido (`slide.slide`) para separarlo entre HomeClass y Online. Los contenidos existentes sin valor quedan visibles en HomeClass.
- `irg_online_section_ids`: secciones nativas del canal cuyo `allowed_batch_ids` intersecta con los lotes Online.
- `irg_online_variant_id`: primera variante del producto del curso detectada como Online por el atributo `modalidad`.
- `irg_has_homeclass` / `irg_has_online`: banderas que controlan la visibilidad de pestañas.

## Vistas y UI

- `views/slide_channel_views.xml` hereda `website_slides.view_slide_channel_form`.
- Inserta un notebook superior nuevo antes del notebook original del canal.
- Mueve las pestañas funcionales existentes del canal dentro de `HomeClass`.
- Construye para `Online` un notebook paralelo con `Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas` y `Secciones iRG`.
- `views/irg_course_convocatoria_views.xml` define además:
  - vista lista del nuevo modelo,
  - vista formulario con notebook de secciones,
  - acción de ventana `action_irg_course_convocatoria`.

## Seguridad

- `security/ir.model.access.csv` crea un único permiso para `irg.course.convocatoria`.
- Grupo afectado: `base.group_user`.
- Permisos concedidos: lectura, escritura, creación y borrado.

## Cómo interactúa con la estructura existente de eLearning y cursos

- `website_slides` sigue siendo la base del curso: `slide.channel` continúa siendo el contenedor principal del curso eLearning.
- `irg_op_course_modality` define el catálogo de modalidades y el campo `irg_modality_ids` en `op.course`; este módulo se apoya en esa capa en lugar de duplicarla.
- `irg_elearning_editable_sections` aporta la pestaña "Secciones iRG" y el uso de `allowed_batch_ids` en las secciones nativas.
- `openeducat_core` aporta `op.batch`, que se filtra por modalidad y curso.
- El módulo no altera matrícula, venta ni progreso; reorganiza la lectura de backoffice del canal según la estructura académica real.

## Dependencias externas

- `website_slides`: modelo `slide.channel` y formulario backend del curso eLearning que se hereda.
- `openeducat_core`: modelo `op.batch` usado para calcular HomeClass y Online.
- `irg_op_course_modality`: catálogo `irg.course.modality` y campo `op.course.irg_modality_ids`.
- `irg_elearning_editable_sections`: modelo `irg.slide.section` y pestaña `irg_sections` sobre la que se inserta la nueva UI.

## Riesgos y notas técnicas

- El `xpath` depende de que `irg_elearning_editable_sections` siga aportando la página `name="irg_sections"`. Si esa vista cambia, la inserción de las pestañas HomeClass y Online dejará de aplicarse.
- La detección de HomeClass depende del nombre de `op.batch.modality_id` y la detección de Online usa nombre de modalidad o patrón `ONL` en código de lote, excluyendo `MONL`.
- La variante Online se detecta por atributo de producto; si el producto del curso no usa ese esquema de atributos, el campo quedará vacío.
- El modelo `irg.course.convocatoria` permanece en el módulo como capa auxiliar heredada de la primera iteración, pero la UI principal ya no depende de él.
- No se detectan `sudo()`, SQL raw, crons ni endpoints HTTP en este módulo.

## Historial reciente

Según el rastro documental reciente del repositorio, el commit `546761091fa95303737e6385d7f105a9433a683c` no introdujo cambios de código en el módulo, sino únicamente la micro-spec y el changelog asociados. La introducción del código de `irg_course_convocatorias` corresponde al commit inmediatamente anterior.

Artefactos relacionados:

- `doc/micro-specs/2026-05-13-irg_course_convocatorias.md`
- `CHANGELOG_2026-05-13_irg_course_convocatorias.md`

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_course_convocatorias \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_course_convocatorias \
    --stop-after-init --db_host=pgodoo_latest
```

## Riesgo operativo al actualizar

La actualización es de bajo impacto sobre datos existentes porque `convocatoria_id` en `irg.slide.section` es opcional y usa `ondelete='set null'`. Aun así, conviene revisar tras la actualización que:

- las pestañas HomeClass y Online aparezcan en el formulario del curso,
- el `xpath` siga aplicándose sobre la pestaña `Secciones iRG`,
- las secciones existentes sin convocatoria continúen visibles en el flujo previo.