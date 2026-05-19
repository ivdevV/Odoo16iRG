# Changelog 2026-05-13 — irg_course_convocatorias

## 2026-05-19 — Corrección detección HomeClass en NC y Neurodesarrollo

- Los cursos relacionados del canal ahora también se detectan desde los lotes asignados en `allowed_batch_ids` de contenidos y secciones, no solo desde asignaturas o `slide_channel_ids`.
- La detección de lotes HomeClass revisa `name`, `code`, `new_code` y `analytic_code` de `op.batch.modality_id`, además del código del lote.
- Si un lote tiene `teams_link` y no está marcado explícitamente como Online, se considera HomeClass para que aparezcan sus enlaces de clase.
- Este ajuste evita que cursos como Neuropsicología Clínica y Neurodesarrollo queden sin lotes/secciones HomeClass por diferencias en codificación de modalidad.
- Versión del módulo actualizada a `16.0.1.4.0`.

## 2026-05-19 — Corrección de copia HomeClass → Online

- El botón `Copiar contenido de HomeClass` crea copias Online independientes conservando nombre, tipo, estado publicado y datos normales de copia.
- Las secciones/categorías se copian antes internamente para poder remapear `category_id`, `parent_slide_id` e `irg_section_id`, pero la secuencia final conserva el orden visual del bloque HomeClass copiado dentro de Online.
- `HomeClass > Contenido` mantiene el campo nativo `slide_ids` para compatibilidad con vistas heredadas de otros módulos y aplica dominio/contexto por modalidad HomeClass.
- La copia ya no reescribe ni limpia `allowed_batch_ids`; no transforma lotes durante una operación cuyo objetivo es copiar contenido.
- La pestaña de secciones HomeClass filtra por modalidad HomeClass/sin modalidad, evitando que las secciones Online copiadas aparezcan o alteren el orden visible de HomeClass.
- Versión del módulo actualizada a `16.0.1.3.0`.

## 2026-05-19 — Hotfix actualización de vista

- Se restaura el nombre nativo `slide_ids` en `HomeClass > Contenido` para no romper XPaths de módulos que heredan `website_slides.view_slide_channel_form`, como `connect_chatgpt`.
- El filtro de modalidad se conserva mediante `domain` y `context`, sin renombrar el campo en la arquitectura final de la vista.
- Versión del módulo actualizada a `16.0.1.3.0`.

## Nuevo módulo: `addons-extra/extrairg/irg_course_convocatorias`

### Qué se hizo

- **Corrección de enfoque funcional** — la UI de `slide.channel` ya no se apoya en una lista manual de convocatorias creada desde el formulario. Ahora se alimenta de datos reales de `op.course`, `irg_op_course_modality` y `op.batch`.

- **Herencia de `slide.channel`** — añade campos calculados:
  - `irg_related_course_ids`
  - `irg_related_modality_ids`
  - `irg_homeclass_batch_ids`
  - `irg_online_batch_ids`
  - `irg_homeclass_section_ids`
  - `irg_online_variant_id`
  - `irg_has_homeclass`
  - `irg_has_online`

- **Integración con `irg_op_course_modality`** — el módulo depende ahora del catálogo de modalidades existente en `op.course` en vez de inventar una gestión paralela para HomeClass y Online.

- **Vistas backend** — dos pestañas nuevas en el formulario de `slide.channel`:
  - **HomeClass**: ahora es una pestaña superior que contiene dentro el notebook original del canal (`Contenido`, `Descripción`, `Opciones`, `Karma`, `Asignaturas`, `Secciones iRG`).
  - **Online**: ahora es una pestaña superior con notebook interno propio y subpestañas equivalentes para datos online.

- **Nuevo campo calculado `irg_online_section_ids`** — permite mostrar una pestaña `Secciones iRG` específica para Online filtrando `allowed_batch_ids` contra lotes online.

- **Nuevo campo calculado `irg_online_content_ids`** — la pestaña `Online > Contenido` deja de mostrar lotes y pasa a trabajar con contenidos `slide.slide` del canal marcados como Online.

- **`Online > Contenido` vuelve al modelo nativo de contenidos** — la pestaña pasa a renderizar `slide_ids` con dominio por modalidad, recuperando el comportamiento estándar del editor de contenidos del canal en lugar de una lista calculada de solo lectura.

- **Separación real por modalidad en `slide.slide`** — se añade `irg_content_modality` a `slide.slide` para separar contenidos HomeClass y Online dentro del mismo canal. `HomeClass > Contenido` muestra contenidos sin modalidad o HomeClass; `Online > Contenido` muestra y crea contenidos con modalidad Online.

- **Campo editable propio para Online** — `Online > Contenido` deja de duplicar el campo `slide_ids` en el mismo formulario y usa `irg_online_slide_ids`, un `one2many` técnico contra `slide.slide/channel_id` con dominio Online. Esto evita que el cliente web reutilice el mismo dataset visual que HomeClass.

- **Creación de secciones en Online** — el árbol de `Online > Contenido` incorpora los botones `Añadir contenido` y `Añadir sección`; las secciones creadas desde ahí nacen con `is_category=True`, categoría `article` y modalidad Online.

- **Dependencia nueva** — se añade `isep_elearning_custom` al manifest porque la nueva estructura reutiliza explícitamente `op_subject_ids` y la pestaña `Asignaturas` dentro del notebook por modalidad.

- **Seguridad** — `ir.model.access.csv` con acceso completo a `irg.course.convocatoria` para `base.group_user`.

### Archivos creados

```
addons-extra/extrairg/irg_course_convocatorias/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── irg_course_convocatoria.py
│   ├── irg_slide_section.py
│   ├── slide_slide.py
│   └── slide_channel.py
├── security/
│   └── ir.model.access.csv
└── views/
    ├── irg_course_convocatoria_views.xml
    └── slide_channel_views.xml
```

### Sin cambios en módulos nativos ni en `addons_uisep`

### Nota importante

- El modelo `irg.course.convocatoria` sigue existiendo en el módulo, pero la UI principal del formulario del canal ya no depende de ese flujo manual para HomeClass y Online.
- La UX pasa de un esquema plano de pestañas a un esquema jerárquico: pestañas de modalidad arriba, subpestañas funcionales dentro.

### Comando de instalación

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> \
  -i irg_course_convocatorias --stop-after-init --db_host=pgodoo_latest
```
