# Execution — irg-student-activity

## Runtime

- Compose: `docker-compose.local.yml` (repo root).
- Base de pruebas: `test_irg_student_activity`.
- `docker compose exec odoo_local` no usable cuando el puerto `8069` está
  ocupado; las corridas de módulo usaron `docker compose run --rm --no-deps
  odoo_local` (misma imagen, config y montaje de addons).
- Durante Task 3, `docker compose build` falló en `apt-get install` (404 en
  paquetes `debian-security` arm64). El orquestador desbloqueó reconstruyendo
  la imagen con snapshot Debian; no se modificó el Dockerfile en esta misión.

## Comando canónico de pruebas

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_student_activity \
  -u irg_student_activity --test-enable --test-tags=/irg_student_activity \
  --stop-after-init --http-port=8099 --log-level=test
```

Primera instalación (Task 1 GREEN): sustituir `-u` por `-i irg_student_activity`.

## TDD por tarea (coding)

| Tarea | RED | GREEN |
| --- | --- | --- |
| 1 Scaffold + acceso | Módulo ignorado sin manifest → 0 tests (`artifacts/task-1-red.txt`) | 2 tests OK (`artifacts/task-1-green.txt`) |
| 2 Campus | 1 failed / 3 tests (`artifacts/task-2-red.txt`) | 3 tests OK (`artifacts/task-2-green.txt`) |
| 3 Evaluaciones + límite 500 | Docker build bloqueado (`artifacts/task-3-docker-blocked.txt`); intento 0 tests (`task-3-green-attempt.txt`) | 5 tests OK (`artifacts/task-3-green.txt`) |
| 4 UI + CSV | 1 failed, 2 errors / 8 tests (`artifacts/task-4-red.txt`) | 8 tests OK (`artifacts/task-4-green.txt`) |
| 5 Docs | — | README + este execution stub |

## Implementación (Tasks 1–4)

- TransientModel de líneas, ensamblador campus + evaluaciones, tope 500,
  pestaña Actividad readonly, export CSV con control Facultad server-side.
- Sin commit (usuario no autorizó).

## Validación (validador independiente, 2026-10-16)

- Comando canónico re-ejecutado fuera de sandbox (docker requiere acceso al
  socket): `0 failed, 0 error(s) of 11 tests`, exit 0. Evidencia:
  `artifacts/validation-tests.txt`.
- Scope: `isep_student_access` no modificado (solo dependencia en manifest);
  código funcional solo en `irg_student_activity`. `irg_hide_portal_servicios`
  aparece modificado en el árbol pero es ajeno a esta misión.
- py_compile y parseo XML OK.
- E2E (TestSprite) obligatorio por scope; diferido al `e2e-tester`. En
  `verification.json` figura `skipped` hasta que el orquestador lo actualice
  con el veredicto E2E.
- Resultado unit gate: PASS.

## Pendiente (gates misión)

- Review de código independiente.
- Validación: repetir comando canónico + `verification.json`.
- E2E TestSprite si el validador aplica scope web (`projectPath`:
  `addons-extra/extrairg/irg_student_activity`).
