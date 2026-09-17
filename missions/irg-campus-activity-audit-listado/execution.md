# execution.md — irg-campus-activity-audit-listado

- 2026-09-17: El listado real (`listado diplomados (1).xlsx`) tiene columnas `Correo electrónico`, `Curso` (nombre + código entre paréntesis), `Nombre`, `País` y `modalidad`. El wizard por lote no sirve.
- Knowledge citada: `modding_rules_and_email_analysis.md`, `irg_course_completion_progress.md`.
- Plan escrito antes del cambio funcional.
- TDD: parser RED local (el código de curso era el nombre entero; faltaban nombre/país/modalidad). GREEN Docker: `0 failed, 0 error(s) of 15 tests`.
- Review independiente: APPROVE. Hallazgos no bloqueantes (email case-sensitive en SQL, metadatos de listado por email).
- Validación repetida: `0 failed, 0 error(s) of 15 tests` en `test_irg_db`. Parser del Excel real: 565 filas, código `DITGHC2606`.
- Módulo instalado en `odoo16irg_local` (16.0.1.1.0) y reiniciado `odoo16irg_local`.
- Menú: OpenEduCat → Reporting → Informe de actividad. Eliminados botón y binding de lote.
- Versión del addon: `16.0.1.1.0`. Sin commit ni push.

