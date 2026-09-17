# Changelog — irg-business-api-gradebook-certificate

## 16.0.1.2.0 — 2026-09-07

- Nuevo comando de escritura `irg_generate_gradebook_certificate` (preview → approve).
- Genera el PDF con `irg.certificate.wizard.action_generate`.
- El resultado verificado incluye `file_b64` y checksum SHA-256 para que un agente reenvíe el fichero.
- El adjunto permanece `public=False`. Sin mail al alumno y sin factura de portal.
- Parcial admite libreta abierta; final exige `done`. Firmante obligatorio (`dpto_academico` o `raimon`).
- Retención: `result_snapshot` guarda el PDF y `unlink()` de operaciones sigue denegado. No hay cron de purga en esta entrega.
