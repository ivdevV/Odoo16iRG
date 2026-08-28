# Changelog

## 2026-08-18

### Added

- Nuevo módulo `irg_elearning_moodle_category_optional`.
- Override de `slide.channel.category_id` para hacerlo opcional en ORM y vista.
- Pruebas de metadatos, vista y persistencia sin categoría Moodle.
- Documentación de instalación, alcance y consideración sobre sincronización.

### Validation

- Review independiente: `PASS`, sin hallazgos.
- Validación final sobre `origin/Dev_iRG` (`4e57a337a`): siete checks en `pass`, dos en `skipped` justificado y cero fallos.
- Pruebas Odoo: `skipped` porque el daemon Docker no estaba iniciado; la `TransactionCase` queda preparada para ejecutarse en dev/local.
- Gate E2E TestSprite: disparado por el cambio de vista y registrado `skipped` porque Docker/Odoo no respondían y la herramienta TestSprite no estaba disponible; no hubo túnel, subida de código ni uso de credenciales.

### Unchanged

- No se modificó `odoo_moodle_connector`, `irg_partner_gender` ni la lógica de sincronización Moodle.
- No se realizó migración de datos, commit, push, PR ni despliegue.
