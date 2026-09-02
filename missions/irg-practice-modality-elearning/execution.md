# Execution log — irg-practice-modality-elearning

- 2026-09-02: misión abierta. Base `origin/Dev_iRG` `cf0e8fd7e`. Rama `feat/irg-practice-modality-elearning`. Worktree `.worktrees/irg-practice-modality-elearning`.
- 2026-09-02: spec y planes escritos. Knowledge citada: modding rules, resolución curso↔canal, patrón `irg_batch_slide_restrictions`.
- Tier efectivo: `complex`. No hay selector de modelo; capacidad usada = razonamiento alto de esta sesión.
- Commits no autorizados; no se harán hasta OK explícito.
- TDD A: RED `test_enrollment_field_exists` (campo ausente). Fixture de `op.course.lang` = `self.env.user.lang or 'en_US'`. Evidencia: `artifacts/red-module-a.txt`. GREEN A: 10 tests. Evidencia: `artifacts/green-module-a.txt`.
- TDD B: RED campo `irg_required_practice_type`. Canal exige `moodle.categories` y mock de `get_moodle_credentials`. El render QWeb de `website.layout` vía `ir.qweb._render` falla por `main_object` (artefacto de test; HTTP `request.render` inyecta el layout). El test de copia pasó a `view.arch_db`. Evidencia: `artifacts/red-module-b.txt`.
- GREEN A+B combinado: `0 failed, 0 error(s) of 18 tests` en `test_irg_pm_a_red_20260902`. Comando: `docker compose -f docker-compose.local.yml -f .worktrees/irg-practice-modality-elearning/missions/irg-practice-modality-elearning/docker-compose.worktree.yml run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_pm_a_red_20260902 -u irg_student_course_practice_modality,irg_practice_slide_restrictions --test-enable --test-tags /irg_student_course_practice_modality,/irg_practice_slide_restrictions --stop-after-init --workers=0 --http-port=18069 --log-level=test` desde el checkout principal. Evidencia: `artifacts/green-modules.txt`.
- Overlay `run --rm --no-deps`: el servicio compartido `odoo16irg_local` no queda montado al worktree.
- Sintaxis: `python3 -m py_compile` de todos los `.py` nuevos + parse XML stdlib: OK.
- Review 1: REVIEW FAIL. BLOQUEANTE-1: override de `_onchange_parent_slide_apply_limitations` sin `@api.onchange` des-registraba el onchange de `irg_elearning_editable_sections`. BLOQUEANTE-2: fixture de B asumía `moodle.categories`. Informe: `02b-review.md`.
- Corrección TDD: RED `test_onchange_parent_keeps_batch_and_copies_practice` (método no registrado) y `test_allows_when_course_linked_only_via_subject_course_id` (sin `subjects.mapped('course_id')`). Evidencia: `artifacts/red-review-fixes.txt`.
- GREEN tras correcciones: `0 failed, 0 error(s) of 20 tests`. Decorador onchange restaurado; fixture Moodle condicional; resolución de curso por `course_id`; helper `irg_has_practice_requirement`; guarda `irg_skip_parent_propagation` en `_apply_parent_limitations`; cache alumno/cursos en `_get_slide_detail`. MENOR-5 (orden del controlador) no se cambia: hay que bloquear antes de `super()` o se entrega el documento. Evidencia: `artifacts/green-review-fixes.txt`.
- Documentación: `doc/modules/extrairg/irg_student_course_practice_modality.md`, `doc/modules/extrairg/irg_practice_slide_restrictions.md`, knowledge `irg_practice_modality_elearning.md`, `CHANGELOG.md`. Spec alineada (fail-closed de sección y orden del GET).
- Review 2: REVIEW OK. Validación independiente: PASS global, 20 tests en base desechable `-i`. `verification.json` `passed`. `e2e_testsprite` skipped (TestSprite MCP no conectado); publicación bloqueada hasta E2E.
- Sin commit, push ni PR.
