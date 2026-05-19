# irg_course_convocatorias

**Categoría:** extrairg
**Versión:** 16.0.1.1.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `website_slides`, `openeducat_core`, `irg_op_course_modality`, `isep_elearning_custom`, `irg_elearning_editable_sections`

---

## ¿Qué hace este módulo?

Añade una capa de lectura académica sobre los cursos de eLearning (`slide.channel`) para separar visualmente la información HomeClass y Online usando la estructura real del proyecto. En lugar de crear convocatorias manuales desde el canal, el módulo parte de los cursos `op.course` relacionados, sus modalidades (`irg_op_course_modality`) y sus lotes reales (`op.batch`), y reorganiza el formulario en dos niveles de pestañas.

Las pestañas superiores **HomeClass** y **Online** aparecen por encima de las pestañas funcionales del canal. Dentro de **HomeClass** se reutiliza el notebook real del curso (`Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas`, `Secciones iRG`). Dentro de **Online** se construye un notebook paralelo orientado a lotes, variante y secciones online.

En la práctica, el módulo actúa como puente entre la estructura nativa de `website_slides`, la organización académica de OpenEduCat y el modelo de secciones editables aportado por `irg_elearning_editable_sections`. No expone controladores ni lógica de portal; su impacto es principalmente de backoffice y de modelado de datos para el equipo académico.

La versión `16.0.1.1.0` corrige el flujo de copia de contenido desde HomeClass hacia Online. El botón `Copiar contenido de HomeClass` ya no genera copias que dependan de secciones, categorías o restricciones de lotes HomeClass; crea una rama Online independiente, reconstruye las relaciones internas de jerarquía y evita que las secciones Online reaparezcan dentro de la pestaña HomeClass.

## Funcionalidades principales

- Calcula automáticamente los cursos `op.course` relacionados con el `slide.channel`.
- Lee las modalidades disponibles desde `irg_op_course_modality` en `op.course.irg_modality_ids`.
- Calcula los lotes HomeClass y Online reales a partir de `op.batch.course_id` y `op.batch.modality_id`.
- Calcula la variante Online desde el producto del curso cuando existe una variante con atributo `modalidad = online`.
- Filtra las secciones HomeClass sobre secciones nativas del canal por modalidad y `allowed_batch_ids`; las secciones Online se obtienen desde contenidos nativos marcados con modalidad Online.
- Filtra `Online > Contenido` sobre `slide.slide`, mostrando contenidos marcados con modalidad Online.
- Renderiza `Online > Contenido` usando `irg_online_slide_ids`, un `one2many` técnico contra `slide.slide/channel_id`, para mantener contenidos editables sin duplicar `slide_ids` en el mismo formulario.
- Añade `irg_content_modality` a `slide.slide` para que HomeClass y Online puedan tener contenidos nativos separados dentro del mismo canal.
- Permite crear secciones desde `Online > Contenido` con los mismos defaults estructurales que HomeClass y con modalidad Online.
- Permite copiar contenido HomeClass a Online como registros independientes mediante `action_copy_homeclass_to_online`.
- Ordena la copia creando primero secciones/categorías y después contenidos, para que las relaciones jerárquicas se reasignen contra las copias Online.
- Sustituye o limpia `allowed_batch_ids` durante la copia: usa lotes Online cuando existen y elimina restricciones cuando no hay lotes Online aplicables.
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
- `irg_homeclass_section_ids`: secciones nativas HomeClass del canal cuyo `allowed_batch_ids` intersecta con los lotes HomeClass.
- `irg_online_content_ids`: contenidos del canal visibles para online según `irg_content_modality`.
- `irg_online_slide_ids`: relación editable a `slide.slide` filtrada por modalidad Online, usada por la pestaña `Online > Contenido`.
- `irg_content_modality`: marca en cada contenido (`slide.slide`) para separarlo entre HomeClass y Online. Los contenidos existentes sin valor quedan visibles en HomeClass.
- `irg_online_section_ids`: secciones nativas del canal marcadas con `irg_content_modality = 'online'`.
- `irg_online_variant_id`: primera variante del producto del curso detectada como Online por el atributo `modalidad`.
- `irg_has_homeclass` / `irg_has_online`: banderas que controlan la visibilidad de pestañas.

## Corrección de copia HomeClass -> Online

El botón `action_copy_homeclass_to_online` se ejecuta desde `Online > Contenido` y copia los contenidos HomeClass del canal como nuevos registros `slide.slide`. La copia es independiente: el contenido Online resultante puede editarse sin modificar el contenido HomeClass original.

El flujo corregido sigue este orden:

1. Selecciona únicamente contenidos HomeClass mediante `_irg_is_homeclass_content`, que considera HomeClass explícito y contenidos antiguos sin modalidad (`False`).
2. Ordena la copia con `_irg_order_slides_for_online_copy`: primero secciones/categorías (`is_category`) y después el resto de contenidos, ambos por `sequence` e `id`.
3. Duplica las secciones iRG relacionadas mediante `_irg_copy_irg_sections_for_online` y conserva un mapa original -> copia para poder reasignar contenidos.
4. Copia cada `slide.slide` con `irg_content_modality = 'online'` e `is_published = False`.
5. Reasigna `category_id`, `parent_slide_id` e `irg_section_id` contra las copias Online ya creadas. Si el padre, categoría o sección original no tiene copia correspondiente, la relación queda vacía para evitar enlaces cruzados con HomeClass.
6. Sustituye `allowed_batch_ids` por los lotes Online calculados en `irg_online_batch_ids`; si no hay lotes Online, limpia el campo con `(5, 0, 0)` para no arrastrar restricciones HomeClass.

Esta corrección evita tres problemas operativos: documentos Online colgados de categorías HomeClass, contenidos Online visibles por lotes HomeClass y secciones Online que reaparecían en HomeClass o alteraban su orden visible.

### Filtrado de secciones HomeClass por modalidad

La pestaña `HomeClass > Secciones iRG` aplica ahora un dominio sobre `irg_native_section_ids` para mostrar solo secciones sin modalidad o con `irg_content_modality = 'homeclass'`. Además, el cálculo `irg_homeclass_section_ids` filtra secciones que sean HomeClass y cuyos `allowed_batch_ids` intersecten con lotes HomeClass reales.

Con esto, las secciones copiadas a Online quedan fuera del flujo HomeClass aunque compartan el mismo canal `slide.channel`.

## Vistas y UI

- `views/slide_channel_views.xml` hereda `website_slides.view_slide_channel_form`.
- Inserta un notebook superior nuevo antes del notebook original del canal.
- Mueve las pestañas funcionales existentes del canal dentro de `HomeClass`.
- Construye para `Online` un notebook paralelo con `Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas` y `Secciones iRG`.
- Añade en `Online > Contenido` el botón `Copiar contenido de HomeClass`, que llama a `action_copy_homeclass_to_online` y muestra una notificación de éxito con el número de elementos copiados.
- Aplica un dominio en `HomeClass > Contenido` para mostrar contenidos sin modalidad o con modalidad HomeClass.
- Aplica un dominio en `HomeClass > Secciones iRG` para mostrar secciones sin modalidad o con modalidad HomeClass, evitando que las secciones Online copiadas se mezclen en el listado HomeClass.
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
- La copia HomeClass -> Online no publica automáticamente los contenidos copiados (`is_published = False`) para permitir revisión editorial antes de exponerlos.
- La reasignación de `category_id`, `parent_slide_id` e `irg_section_id` depende del orden secciones/categorías antes que contenidos; cambiar ese orden reintroduciría relaciones cruzadas con HomeClass.
- El modelo `irg.course.convocatoria` permanece en el módulo como capa auxiliar heredada de la primera iteración, pero la UI principal ya no depende de él.
- No se detectan `sudo()`, SQL raw, crons ni endpoints HTTP en este módulo.

## Historial reciente

El changelog del módulo registra el 2026-05-19 la corrección del botón `Copiar contenido de HomeClass`. El cambio documentado actualiza el módulo a `16.0.1.1.0` y centra la mejora en hacer que la copia HomeClass -> Online sea estructuralmente independiente.

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
- las secciones existentes sin convocatoria continúen visibles en el flujo previo,
- al usar `Copiar contenido de HomeClass`, los nuevos contenidos Online no conserven `allowed_batch_ids` HomeClass,
- las relaciones `category_id`, `parent_slide_id` e `irg_section_id` de los contenidos Online apunten a copias Online o queden vacías si no hay copia equivalente,
- las secciones Online copiadas no aparezcan en `HomeClass > Secciones iRG`.