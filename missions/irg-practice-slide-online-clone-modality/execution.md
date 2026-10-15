# Execution log — irg-practice-slide-online-clone-modality

- 2026-10-15: misión abierta tras diagnóstico. Jev `skipped` (`http_error`). Tier `standard`, misión `full`.
- Knowledge: `irg_practice_modality_elearning.md`, `irg_elearning_online_clone_resolution.md`.
- Plan: `plan.md`. Sin commit/push/PR hasta OK explícito.
- Base commit al abrir: `30a6f9383` (rama de trabajo local; cambios de otras misiones no forman parte de este alcance).
- Runtime: imagen `odoo16irg:16.0-local` vía `docker exec odoo16irg_local` (compose build fallaba por apt 404 Debian 11; el servicio local quedó Up). Tests con `-i irg_course_convocatorias,irg_practice_slide_restrictions` para disponer de `irg_homeclass_channel_id`.
- TDD RED: `test_online_clone_allows_matching_modality_via_homeclass` FAIL (`False is not true`). Evidencia: `artifacts/red-tests.txt` (`1 failed, 0 error(s) of 14 tests`).
- GREEN: `_irg_resolution_channel()` usa `irg_homeclass_channel_id` si existe; bump `16.0.1.2.0`. Evidencia: `artifacts/green-tests.txt` (`0 failed, 0 error(s) of 14 tests`). Los tres tests de clon corrieron.
- Review (agente distinto): REVIEW OK. Informe `02b-review.md`. Hallazgo MENOR no bloqueante: en clon solo se consultan cursos del maestro (no unión con enlaces directos del clon); documentado en limitaciones.
- Validación independiente: `verification.json` `passed`. Evidencia `artifacts/validation-tests.txt`, `artifacts/syntax-py-compile.txt`. `e2e_testsprite` skipped por scope. BDs desechables eliminadas.
- Documentación: `doc/modules/extrairg/irg_practice_slide_restrictions.md`, knowledge `irg_practice_modality_elearning.md`, `CHANGELOG.md`. Sin cambios de código en Documentación.
- Publicación: pendiente de OK explícito (commit/push/PR). Tras `-u irg_practice_slide_restrictions` en la BD operativa, probar con Usuario Prueba 1 (matrícula 907, tipo 6) en canal 319.
