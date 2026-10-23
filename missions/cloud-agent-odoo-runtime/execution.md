# Execution — runtime local de Cloud Agents

## 2026-10-23 — Plan

- Rama de trabajo: `cursor/cloud-agent-odoo-runtime-9bea`, desde `Dev_iRG` en `acb64787a` (merge del PR #52). `origin/Dev_iRG` coincide; behind 0.
- Clasificación: misión `full`, tier `standard`. Security Advisor pendiente antes de crear `.cursor/` o instalar Docker.
- `environment-info`: entorno personal `e45fa8d1-ce18-11f1-89ee-7aa6f0729b11`, `environmentJsonPath` null, egress sin restricción. La rama por defecto de GitHub es `main`.
- VM: Ubuntu 24.04, sin Docker, `/dev/fuse` presente, `sudo` sin contraseña, Node en `/exec-daemon/node`, TestSprite MCP `ready`.
- `.gitignore` ignora `docker-compose*.yml` y `etc/`. No hay `docker-compose.local.yml` en el árbol.
- Cierre de `irg_oral_case`: 16 módulos del repo, sin `external_dependencies`. Los módulos de núcleo ausentes del repo vienen en `odoo:16.0`.

## Decisiones

- Docker-in-Docker según la sección Running Docker de la documentación de Cursor (2026-10-23), no Odoo instalado en el host: `AGENTS.md` exige `docker-compose.local.yml`.
- El compose de la raíz se genera y permanece ignorado. La plantilla vive en `.cursor/runtime/` para no chocar con el gitignore.
- No se reutiliza la imagen ni la contraseña del compose de despliegue.
- TDD del contrato de configuración: sí, con unittest en la misión. La prueba real de Odoo no cabe en ese unittest; va a Validación.

## 2026-10-23 — Security Advisor, ronda 1

- Veredicto `[NO]` en `artifacts/security-advisor.txt`.
- Causa: un `docker compose pull` sin `-f` puede leer `docker-compose.yml` de despliegue y sus credenciales.
- El plan se enmienda antes de crear `.cursor/`: `-f docker-compose.local.yml` en todas las invocaciones, `--env-file` propio, materializar antes del pull, centinela exacto, sin `env_file` ni variables de host en el servicio Odoo, y el test de contrato cubre esos rechazos.
- No se ha escrito Dockerfile, script ni compose. Sigue bloqueada la implementación hasta un `[YES]` nuevo.

## 2026-10-23 — Security Advisor, ronda 2

- Veredicto `[YES]` en `artifacts/security-advisor-r2.txt`.
- El pull sin `-f` queda cerrado. Se puede implementar conservando los controles de esa revisión.
- Siguiente paso: RED del test de contrato, antes de crear `.cursor/`.

## 2026-10-23 — TDD del contrato

- RED: `python3 -m unittest missions.cloud-agent-odoo-runtime.tests.test_runtime_contract` salió 5. `setUpClass` no encontró `.cursor/`. Evidencia: `artifacts/red-contract.txt`.
- GREEN: el mismo comando, 8 tests, exit 0. Evidencia: `artifacts/green-contract.txt`.
- Pin de Docker confirmado en el repo apt de noble: `5:28.5.2-1~ubuntu.24.04~noble` (el del snippet de Cursor). Node 22.23.4 en `/usr/local` dentro del Dockerfile.
- Alias de red `db` en `pgodoo_local`: el entrypoint oficial de `odoo:16.0` reescribe `db_host` con el default `db` si no hay variable `HOST`. No se pasa el entorno del host. El conf versionado sigue diciendo `pgodoo_local` para quien lea el archivo; la resolución `db` queda dentro de la red de compose.
- `bash .cursor/install.sh` lanzado en tmux `odoo-runtime-install`. Log: `artifacts/install-1.txt`.

## 2026-10-23 — Install, arranque y tests de irg_oral_case

- Primer `apt-get` se detuvo en el prompt de `/etc/fuse.conf`. Se añadió `--force-confdef` y `--force-confold` a `.cursor/install-docker-packages.sh` y se relanzó. Evidencia del atasco: `artifacts/install-1.txt`. Evidencia del install bueno: `artifacts/install-2.txt` (EXIT 0).
- Segunda ejecución de `install.sh` (idempotencia): `artifacts/install-idempotent.txt`, INSTALL_EXIT 0. Las tres imágenes quedaron en caché.
- `start.sh`: `artifacts/start.txt`, START_EXIT 0. `pgodoo16irg_local` healthy. `docker info` ok.
- Entrypoint real de `odoo:16.0` (`/entrypoint.sh`): si `odoo.conf` ya tiene `db_host`, usa ese valor (`pgodoo_local`) y no el default `db`. El alias `db` no hizo falta en esta corrida. La línea de log fue `database: odoo@pgodoo_local:5432`.
- Tests, base desechable `test_irg_oral_case_9bea`, sin tocar el módulo:

```
docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_oral_case_9bea -i irg_oral_case --test-enable --test-tags=/irg_oral_case --stop-after-init --workers=0 --http-port=8099 --log-level=test
```

- Resultado Odoo: `0 failed, 2 error(s) of 20 tests`. ODOO_EXIT 1. Log: `artifacts/odoo-irg-oral-case-tests.txt`.
- Errores, sin arreglar (prohibido en esta PR):
  - `TestOralCaseGrade.test_student_cannot_write_the_suggestion_or_the_official_grade`: `TypeError: issubclass() arg 1 must be a class` en `assertRaises((AccessError, MissingError))`.
  - `TestOralCaseGrade.test_teacher_confirmation_is_required_and_does_not_copy_the_suggestion`: `AccessError` al leer `slide.slide.oral_case_enabled` desde `wizard/confirm_grade.py`.
- Limpieza: `dropdb` exit 0. `\l` ya no lista la base. Evidencia: `artifacts/cleanup.txt`.
- E2E no se ejecuta: los tests del módulo no están en verde y el plan prohíbe gastar el crédito. `e2e_testsprite` sigue skipped por scope.

## 2026-10-23 — Review y validación

- Review de código, rol distinto: `APPROVED` en `artifacts/review.md`. El revisor reejecutó el contrato (8 ok) y no es el gate de validación.
- Validador independiente: `verification.json` con `status: failed`. El único `fail` es `odoo_irg_oral_case_tests` en `test_irg_oral_case_validator`: `0 failed, 2 error(s) of 20 tests`. Mismos dos tests que la primera corrida. Base borrada (`artifacts/validator-cleanup.txt`).
- No se reabre implementación para tocar `irg_oral_case`: el encargo lo prohíbe. El fallo queda documentado. Los checks de entorno están en `pass`.
- Documentación escrita después, porque el usuario la pidió y el único fail no se puede corregir en esta PR. No cambia código de runtime, así que no se repite Review ni Validación.
