# irg_course_convocatorias

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `website_slides`, `openeducat_core`, `irg_elearning_editable_sections`

---

## ¿Qué hace este módulo?

Añade una capa de gestión académica sobre los cursos de eLearning (`slide.channel`) para separar sus convocatorias por modalidad y año. En lugar de concentrar todas las secciones y lotes del curso en una única estructura, el módulo introduce dos pestañas nuevas en la ficha del curso: **HomeClass** y **Online**.

Cada convocatoria queda registrada como un elemento propio, vinculado al curso eLearning, con sus lotes (`op.batch`) y sus secciones iRG asociadas. Esto permite que un mismo curso reutilice su estructura general en Odoo, pero organice el contenido y la planificación por edición anual sin mezclar convocatorias históricas con nuevas aperturas.

En la práctica, el módulo actúa como puente entre la estructura nativa de `website_slides`, la organización académica de OpenEduCat y el modelo de secciones editables aportado por `irg_elearning_editable_sections`. No expone controladores ni lógica de portal; su impacto es principalmente de backoffice y de modelado de datos para el equipo académico.

## Funcionalidades principales

- Crea el nuevo modelo `irg.course.convocatoria` para representar convocatorias de curso por modalidad (`homeclass` / `online`) y año.
- Añade al curso eLearning (`slide.channel`) dos relaciones O2M separadas: `irg_homeclass_conv_ids` y `irg_online_conv_ids`.
- Permite asociar lotes académicos (`op.batch`) a cada convocatoria para segmentar alumnos o ediciones.
- Permite vincular una variante de producto (`product.product`) a las convocatorias Online mediante `online_variant_id`.
- Reutiliza las secciones editables de `irg.slide.section` y las asigna opcionalmente a una convocatoria concreta mediante `convocatoria_id`.
- Incluye vista lista y formulario propias para `irg.course.convocatoria`, además de la extensión del formulario de `slide.channel`.
- Expone permisos de lectura, escritura, creación y borrado del nuevo modelo para `base.group_user`.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.course.convocatoria` | Nuevo | `name`, `modality`, `year`, `sequence`, `active`, `channel_id`, `batch_ids`, `online_variant_id`, `irg_section_ids`, `section_count` |
| `slide.channel` | Herencia | `irg_homeclass_conv_ids`, `irg_online_conv_ids` |
| `irg.slide.section` | Herencia | `convocatoria_id` |

### Detalle funcional de campos

- `name`: nombre visible de la convocatoria. El `onchange` propone automáticamente un valor del tipo "HomeClass 2026" cuando hay modalidad y año y el nombre aún está vacío.
- `modality`: separación operativa entre convocatorias HomeClass y Online.
- `year`: año de referencia de la edición; se modela como `Char`, no como entero.
- `channel_id`: relación obligatoria con el curso eLearning (`slide.channel`). Si el curso se elimina, sus convocatorias se eliminan también (`ondelete='cascade'`).
- `batch_ids`: relación Many2many con `op.batch`, usada para agrupar la convocatoria por lotes/promociones académicas.
- `online_variant_id`: variante comercial asociada a la modalidad Online. Solo se muestra en las vistas Online, aunque no existe una restricción ORM que la obligue fuera de la UI.
- `irg_section_ids`: secciones iRG asociadas a la convocatoria. Estas secciones siguen perteneciendo al canal, pero ahora pueden quedar clasificadas por convocatoria.
- `section_count`: contador calculado a partir de `irg_section_ids`.

## Vistas y UI

- `views/slide_channel_views.xml` hereda `website_slides.view_slide_channel_form`.
- El `xpath` se ancla en la pestaña `page[@name='irg_sections']`, que procede del módulo `irg_elearning_editable_sections`.
- Inserta dos páginas nuevas en el notebook del curso:
  - **HomeClass**: lista convocatorias de modalidad HomeClass, con `sequence`, `name`, `year`, `batch_ids` y `section_count`.
  - **Online**: misma estructura, añadiendo `online_variant_id`.
- En ambas pestañas, cada convocatoria se puede abrir en formulario emergente y gestionar desde ahí sus secciones internas.
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
- `irg_elearning_editable_sections` aporta el modelo `irg.slide.section` y la pestaña previa "Secciones iRG". Este módulo no la reemplaza; la complementa con una clasificación adicional por convocatoria.
- `openeducat_core` aporta `op.batch`, que se usa para asociar una convocatoria a sus lotes o promociones académicas.
- Las secciones asignadas a una convocatoria siguen ligadas al mismo `channel_id`, por lo que la organización por convocatoria convive con la organización global del curso.
- El módulo no altera la lógica de venta, matrícula, publicación ni progreso del alumno. Su objetivo es estructurar mejor el backoffice del contenido y la planificación académica.

## Dependencias externas

- `website_slides`: modelo `slide.channel` y formulario backend del curso eLearning que se hereda.
- `openeducat_core`: modelo `op.batch` usado en `batch_ids`.
- `irg_elearning_editable_sections`: modelo `irg.slide.section` y pestaña `irg_sections` sobre la que se inserta la nueva UI.

## Riesgos y notas técnicas

- El `xpath` depende de que `irg_elearning_editable_sections` siga aportando la página `name="irg_sections"`. Si esa vista cambia, la inserción de las pestañas HomeClass y Online dejará de aplicarse.
- `year` es un `Char` y el orden del modelo usa `year desc`; si se cargan valores no homogéneos, la ordenación puede no reflejar correctamente la cronología esperada.
- `online_variant_id` solo se exige en determinadas vistas, pero no existe una validación Python o SQL que obligue a rellenarlo para convocatorias Online creadas por importación, RPC o vistas alternativas.
- El acceso completo para `base.group_user` simplifica la operativa, pero amplía bastante la superficie de edición del modelo.
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