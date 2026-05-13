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
  - **HomeClass**: cursos relacionados, modalidades, lotes HomeClass reales y secciones del curso filtradas por `allowed_batch_ids`.
  - **Online**: cursos relacionados, modalidades, lotes Online reales y variante Online detectada desde el producto del curso.

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

### Comando de instalación

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> \
  -i irg_course_convocatorias --stop-after-init --db_host=pgodoo_latest
```
