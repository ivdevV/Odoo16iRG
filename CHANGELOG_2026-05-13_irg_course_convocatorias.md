# Changelog 2026-05-13 — irg_course_convocatorias

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

- **Nuevo campo calculado `irg_online_content_ids`** — la pestaña `Online > Contenido` deja de mostrar lotes y pasa a mostrar contenidos `slide.slide` del canal filtrados para online, manteniendo solo estructura visible (`categorías` y `artículos`) y excluyendo materiales tipo documento.

- **`Online > Contenido` vuelve al modelo nativo de contenidos** — la pestaña pasa a renderizar `slide_ids` con dominio sobre `irg_online_content_ids`, recuperando el comportamiento estándar del editor de contenidos del canal en lugar de una lista calculada de solo lectura.

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
