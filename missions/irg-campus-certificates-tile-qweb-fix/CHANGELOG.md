# Changelog — irg-campus-certificates-tile-qweb-fix

## 16.0.1.0.0

- Nuevo módulo `irg_campus_certificates_tile_qweb_fix`.
- El tile «Certificados y Diplomas» deja de usar `hasattr` en QWeb.
- Usa `course_id.is_diplomado()` para ocultarlo en diplomados.
