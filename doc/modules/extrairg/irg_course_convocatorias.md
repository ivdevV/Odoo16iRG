# irg_course_convocatorias

**Categoría:** extrairg
**Versión:** 16.0.2.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `website_slides`, `openeducat_core`, `irg_op_course_modality`, `isep_elearning_custom`, `irg_elearning_editable_sections`

---

## ¿Qué hace este módulo?

Añade una capa de lectura académica sobre los cursos de eLearning (`slide.channel`) para separar visualmente la información HomeClass y Online usando la estructura real del proyecto. En lugar de crear convocatorias manuales desde el canal, el módulo parte de los cursos `op.course` relacionados, sus modalidades (`irg_op_course_modality`) y sus lotes reales (`op.batch`), y reorganiza el formulario en dos niveles de pestañas.

Las pestañas superiores **HomeClass** y **Online** aparecen por encima de las pestañas funcionales del canal. Dentro de **HomeClass** se reutiliza el notebook real del curso (`Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas`, `Secciones iRG`). Dentro de **Online** se construye un notebook paralelo orientado a lotes, variante y secciones online.

En la práctica, el módulo actúa como puente entre la estructura nativa de `website_slides`, la organización académica de OpenEduCat y el modelo de secciones editables aportado por `irg_elearning_editable_sections`. No expone controladores ni lógica de portal; su impacto es principalmente de backoffice y de modelado de datos para el equipo académico.

La versión `16.0.2.0.0` reescribe la acción `action_copy_homeclass_to_online` como un **bootstrap manual 1:1**. La copia ya no se apoya en `slide.slide.copy()`; en su lugar utiliza `create()` directo con una whitelist explícita de campos, vacía deliberadamente `allowed_batch_ids`, clona todas las secciones iRG del canal y replica los quizzes asociados (`slide.question` + `slide.answer`). El bloque copiado se añade siempre al final del listado Online y las ejecuciones repetidas acumulan nuevos bloques sin tocar los anteriores.

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
- Permite copiar contenido HomeClass a Online como registros independientes mediante `action_copy_homeclass_to_online`, ejecutado como bootstrap 1:1 sin reutilizar `slide.slide.copy()`.
- Clona todas las `irg.slide.section` del canal (incluidas las vacías) durante el bootstrap, no sólo las referenciadas por contenidos HomeClass.
- Suspende los hooks de `irg_elearning_editable_sections` durante la clonación mediante el flag de contexto `irg_skip_parent_propagation=True`, evitando reescrituras automáticas de jerarquía o lotes.
- Añade siempre el bloque copiado al final del listado Online calculando la base de secuencia con `_irg_bootstrap_base_sequence`; las ejecuciones repetidas son idempotentes en el sentido de que no tocan los bloques previos.
- Vacía explícitamente `allowed_batch_ids` en cada copia Online para que el equipo académico asigne lotes Online de forma consciente.
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

## Bootstrap HomeClass -> Online (16.0.2.0.0)

El botón `action_copy_homeclass_to_online` se ejecuta desde `Online > Contenido` y reconstruye los contenidos HomeClass del canal como nuevos registros `slide.slide` en modalidad Online. La copia es estructuralmente independiente: el contenido Online resultante puede editarse sin tocar el HomeClass original.

El flujo se reescribió completamente en `16.0.2.0.0` para eliminar el uso de `slide.slide.copy()` y trabajar con `create()` directo controlado:

1. **Selección y orden.** Filtra contenidos HomeClass con `_irg_is_homeclass_content` (HomeClass explícito o sin modalidad asignada) y los ordena por `(sequence, id)`. Si no hay contenido elegible se emite una notificación `warning` y la acción termina.
2. **Suspensión de hooks.** Crea un entorno con `irg_skip_parent_propagation=True` para todo el bootstrap. Mientras está activo, `irg_elearning_editable_sections` no aplica `_apply_parent_hierarchy`, `_apply_parent_limitations` ni los onchange asociados.
3. **Clonado de secciones iRG.** `_irg_bootstrap_clone_irg_sections` duplica **todas** las `irg.slide.section` del canal (incluidas las vacías), conservando `name`, `sequence` y `active`. `convocatoria_id` queda vacío en las copias. Devuelve un mapa original -> copia.
4. **Base de secuencia.** `_irg_bootstrap_base_sequence` obtiene la mayor secuencia Online actual; las copias se insertan a partir de ahí en pasos de 10, de modo que el bloque queda al final del listado Online.
5. **Pase 1 — Crear.** Primero las categorías HomeClass, luego el resto de slides. Cada copia se crea con `_irg_bootstrap_prepare_slide_values`, que aplica la whitelist `_irg_bootstrap_slide_clone_fields()`, fija `channel_id`, marca `irg_content_modality='online'`, vacía `allowed_batch_ids` con `(5,)` y deja `category_id`, `parent_slide_id` e `irg_section_id` sin asignar.
6. **Pase 2 — Remapear.** Con el mapa completo, `_irg_bootstrap_remap_values` reescribe `category_id`, `parent_slide_id` e `irg_section_id` apuntando a las copias Online correspondientes. Si el original no tiene equivalente, la referencia queda en `False` para no enlazar contra HomeClass.
7. **Pase 3 — Quizzes.** `_irg_bootstrap_clone_quizzes` replica `slide.question` y `slide.answer` de cada slide copiado, manteniendo `sequence`, `question`, `text_value`, `is_correct` y `comment`.
8. **Notificación.** Se centraliza en `_irg_bootstrap_notification`: tipo `success` con el número de copias creadas o `warning` cuando el canal no tiene HomeClass elegible.

Esta arquitectura evita los efectos colaterales de `copy()` (regeneración de relaciones técnicas de `website_slides`, propagación cruzada de jerarquía, copia de lotes HomeClass a Online) y produce un bloque Online predecible que el equipo académico puede editar y asignar a lotes manualmente.

### Whitelist de campos clonados

`_irg_bootstrap_slide_clone_fields()` define los campos que se copian en el pase 1. Su contenido actual es:

```
name, description, slide_category, is_category, is_published, url,
document_google_url, mime_type, datas, image_1920, html_content,
video_url, embed_code, completion_time, access_token,
quiz_first_attempt_reward, quiz_second_attempt_reward,
quiz_third_attempt_reward, quiz_fourth_attempt_reward,
inherit_limitations_from_parent, scheduled_date
```

Cada campo se verifica con `_fields` antes de leerse, así que la lista puede contener campos opcionales o de terceros. `access_token` se excluye deliberadamente al construir los valores para evitar colisiones; `tag_ids` se replica como `(6, 0, ids)` y `allowed_batch_ids` se vacía con `(5,)`.

La whitelist está pensada para **extenderse por herencia**: cualquier módulo que añada un campo obligatorio a `slide.slide` debería sobrecargar `_irg_bootstrap_slide_clone_fields()` y añadirlo. Si no se hace y el campo no tiene `default`, el `create()` del pase 1 puede romper. Es el único riesgo conocido del bootstrap.

### Filtrado de secciones HomeClass por modalidad

La pestaña `HomeClass > Secciones iRG` aplica ahora un dominio sobre `irg_native_section_ids` para mostrar solo secciones sin modalidad o con `irg_content_modality = 'homeclass'`. Además, el cálculo `irg_homeclass_section_ids` filtra secciones que sean HomeClass y cuyos `allowed_batch_ids` intersecten con lotes HomeClass reales.

Con esto, las secciones copiadas a Online quedan fuera del flujo HomeClass aunque compartan el mismo canal `slide.channel`.

## Vistas y UI

- `views/slide_channel_views.xml` hereda `website_slides.view_slide_channel_form`.
- Inserta un notebook superior nuevo antes del notebook original del canal.
- Mueve las pestañas funcionales existentes del canal dentro de `HomeClass`.
- Construye para `Online` un notebook paralelo con `Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas` y `Secciones iRG`.
- Añade en `Online > Contenido` el botón `Copiar contenido de HomeClass`, que llama a `action_copy_homeclass_to_online`. El texto de confirmación advierte que se crean nuevos registros al final del listado Online sin modificar los existentes y que los lotes permitidos quedan vacíos en las copias. La acción muestra una notificación `success` con el número de elementos copiados o `warning` si no había HomeClass elegible.
- El árbol de `Online > Contenido` aplica `decoration-muted="is_category"` para marcar visualmente las filas que son categorías/secciones sin cambiar su comportamiento funcional.
- `HomeClass > Contenido` mantiene el campo nativo `slide_ids` para que otros módulos puedan seguir heredando sus anclas XPath, y aplica un dominio para mostrar solo contenidos sin modalidad o con modalidad HomeClass.
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
- El bootstrap `action_copy_homeclass_to_online` conserva el estado de publicación porque `is_published` está en la whitelist; los lotes permitidos se vacían deliberadamente y deben asignarse a mano.
- La reasignación de `category_id`, `parent_slide_id` e `irg_section_id` se hace en un pase separado contra el mapa de copias completo; si el original no tiene equivalente Online, la referencia queda vacía.
- **Whitelist y campos obligatorios:** si otro módulo añade un campo `required=True` sin `default` a `slide.slide` y no extiende `_irg_bootstrap_slide_clone_fields()`, el `create()` del pase 1 puede fallar. La extensión recomendada es sobrecargar ese método y añadir el campo.
- El bootstrap se ejecuta con `irg_skip_parent_propagation=True`; si otro módulo añade hooks similares a `_apply_parent_hierarchy`, debería respetar el mismo flag para no reintroducir reescrituras automáticas durante la clonación.
- El modelo `irg.course.convocatoria` permanece en el módulo como capa auxiliar heredada de la primera iteración, pero la UI principal ya no depende de él.
- No se detectan `sudo()`, SQL raw, crons ni endpoints HTTP en este módulo.

## Tests

El módulo incluye `tests/test_bootstrap_online.py` (`TransactionCase`, tag `irg_course_convocatorias`, `post_install`) con la siguiente cobertura:

- `test_bootstrap_creates_independent_online_copies`: verifica que se crea un slide Online por cada slide HomeClass elegible y que los registros HomeClass originales conservan id y `sequence`.
- `test_bootstrap_remaps_hierarchy_within_online`: verifica que `category_id` y `parent_slide_id` de las copias Online apuntan a las copias Online, no a los originales HomeClass.
- `test_bootstrap_clones_all_irg_sections`: verifica que se clonan todas las `irg.slide.section` del canal (incluidas las vacías), duplicando el conteo total.
- `test_bootstrap_empty_when_no_homeclass`: verifica que un canal sin HomeClass devuelve una notificación `warning` y no crea slides.
- `test_bootstrap_idempotent_append`: verifica que dos ejecuciones consecutivas duplican el número de slides Online sin tocar el primer bloque.

## Historial reciente

- **2026-05-19 — `16.0.1.3.0`:** primera versión del botón `Copiar contenido de HomeClass`, con copia mediante `slide.slide.copy()` y reasignación posterior de jerarquía. Hotfix de vistas para mantener `slide_ids` como ancla.
- **`16.0.2.0.0`:** reescritura completa de `action_copy_homeclass_to_online` como bootstrap manual 1:1. Se elimina el uso de `copy()` y se introduce la whitelist `_irg_bootstrap_slide_clone_fields()`, el clonado completo de secciones iRG (`_irg_bootstrap_clone_irg_sections`), el cálculo de base de secuencia (`_irg_bootstrap_base_sequence`), la replicación de quizzes (`_irg_bootstrap_clone_quizzes`) y la centralización de la notificación (`_irg_bootstrap_notification`). Se activa `irg_skip_parent_propagation=True` durante todo el bootstrap para suspender los hooks de `irg_elearning_editable_sections`. Las copias quedan siempre al final del listado Online, con `allowed_batch_ids` vacío y referencias jerárquicas remapeadas. El texto del botón `confirm` se actualiza para reflejar este comportamiento. Se añade la carpeta `tests/` con `test_bootstrap_online.py`.

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
- al usar `Copiar contenido de HomeClass`, el bloque Online se añada al final sin modificar los registros HomeClass ni los bloques Online previos,
- las copias Online queden con `allowed_batch_ids` vacío y con `category_id`, `parent_slide_id` e `irg_section_id` apuntando a copias Online o vacíos,
- todas las `irg.slide.section` del canal aparezcan duplicadas tras el bootstrap,
- los quizzes (`slide.question`/`slide.answer`) asociados a slides HomeClass tengan equivalente en las copias Online,
- las secciones Online copiadas no aparezcan en `HomeClass > Secciones iRG`.