# Changelog 2026-05-13 — irg_course_convocatorias

## Nuevo módulo: `addons-extra/extrairg/irg_course_convocatorias`

### Qué se hizo

- **Nuevo modelo `irg.course.convocatoria`** — gestiona convocatorias de un curso (`slide.channel`) por modalidad (`homeclass` / `online`) y año. Incluye `batch_ids` (lotes `op.batch`), `online_variant_id` (variante de producto) y `irg_section_ids` (secciones del curso).

- **Herencia de `slide.channel`** — añade dos campos O2M filtrados:
  - `irg_homeclass_conv_ids` (domain `modality=homeclass`)
  - `irg_online_conv_ids` (domain `modality=online`)

- **Herencia de `irg.slide.section`** — añade campo `convocatoria_id` (Many2one a `irg.course.convocatoria`, opcional, `ondelete=set null`). Las secciones existentes no se ven afectadas.

- **Vistas backend** — dos pestañas nuevas en el formulario de `slide.channel`:
  - **HomeClass**: lista de convocatorias anuales HC con lotes y contador de secciones; form popup con pestaña de secciones interna.
  - **Online**: igual pero con campo `online_variant_id` para vincular la variante online del producto.

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

### Comando de instalación

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> \
  -i irg_course_convocatorias --stop-after-init --db_host=pgodoo_latest
```
