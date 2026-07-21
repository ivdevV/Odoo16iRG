# Task 1 report — IRG Partner Safe Merge

## Resultado de implementación

Se creó exclusivamente el addon nuevo `addons-extra/extrairg/irg_partner_safe_merge`; no se editó ningún addon existente. Incluye acción contextual administrativa, wizard con recomendación/preview/conflictos/confirmación, allowlist cerrada, inventario bloqueante, locks deterministas, hash de preview, transferencias ORM, unión semántica de categorías/followers, protección del origen y auditoría inmutable.

## Archivos creados

- `__init__.py`, `__manifest__.py`.
- `models/__init__.py`, `models/res_partner.py`, `models/merge_audit.py`.
- `wizard/__init__.py`, `wizard/partner_safe_merge_wizard.py`.
- `security/ir.model.access.csv`.
- `views/res_partner_views.xml`, `views/partner_safe_merge_wizard_views.xml`, `views/merge_audit_views.xml`.
- `tests/__init__.py`, `tests/test_partner_safe_merge.py`, `tests/test_static_contract.py`.

## Evidencia RED/GREEN

- RED, antes de producción: `C:\Users\admin\.local\bin\python3.11.exe addons-extra\extrairg\irg_partner_safe_merge\tests\test_static_contract.py` → código 1; faltaban los once archivos requeridos y el servicio del wizard.
- Suite Odoo escrita primero: cubre permisos/RPC, selección e identidad, compañía/jerarquía, recomendación, conflictos escalares, grafo de leads-usuario-estudiante, blockers, categorías/followers, cambio de preview, fallos por fase/rollback, idempotencia y modelos inmutables.
- GREEN estático final: el mismo contrato → código 0, `Ran 4 tests ... OK`.
- Odoo RED/ejecución enfocada: `docker compose -f C:\Users\admin\Documents\iRG\Odoo16iRG\docker-compose.local.yml run --rm odoo_local odoo --stop-after-init --test-enable --test-tags /irg_partner_safe_merge -i irg_partner_safe_merge` → código 1 antes de arrancar, daemon ausente en `npipe:////./pipe/docker_engine`.

## Comandos y resultados finales

- `python3.11 -m compileall -q addons-extra\extrairg\irg_partner_safe_merge` → pass, sin salida.
- `python3.11 ...\tests\test_static_contract.py` → pass; AST Python y parseo de todos los XML/CSV incluidos.
- búsqueda de `._merge(`, `cr.commit(` y `DELETE FROM` en producción → pass, sin coincidencias.
- revisión de whitespace de todos los `.py/.xml/.csv` → pass, sin coincidencias.
- `git diff --check` → pass, sin salida.
- `git status --short --untracked-files=all` → solo addon/artefactos/planes nuevos; sin commit, push ni PR.
- Ruff → no disponible (`No module named ruff`), registrado como check no ejecutable sin instalar dependencias.

## Desviaciones y riesgos restantes

- No hay desviación funcional intencional respecto a la micro-spec.
- La instalación del manifest, el catálogo real de modelos/campos, los locks PostgreSQL, las restricciones únicas, recomputaciones stored-related y la suite Odoo completa solo pueden verificarse dentro del runtime Odoo/PostgreSQL. Docker no estaba iniciado, por lo que **el gate de integración Odoo no está pasado**.
- La validación independiente debe arrancar Docker, montar este worktree mediante overlay sobre `docker-compose.local.yml`, instalar el addon en una base de prueba, ejecutar `--test-tags /irg_partner_safe_merge`, y registrar cleanup/restauración. Cualquier incompatibilidad encontrada debe volver a Implementación.
- No se creó commit, no se hizo push y no se abrió PR.

## Corrección tras Review — 2026-07-20

Se corrigieron todos los P1 y el P2 del review independiente:

- Descubrimiento genérico de M2M directos con bloqueo closed-world; única unión aprobada `res.partner.category_id`, con filas relacionales en snapshot/hash y lock SQL explícito.
- Decisiones escalares y enlace exacto usuario-estudiante ligados al plan final. La UI exige elegir y volver a generar preview; confirmación bloquea y revalida el plan antes de mutar.
- Estado generado de wizard/líneas protegido por `env.su` más contexto privado; un contexto RPC por sí solo ya no sirve como frontera interna.
- Coherencia exacta de todas las combinaciones `res.users`/`op.student` y bloqueo de grafos presentes en ambos contactos.
- Inventario, lock y transferencia explícitos para `op.admission.elearning.wizard` aunque sea transient.
- Políticas semánticas explícitas para admisiones, gradebooks, ventas y schedules, con filas source/target incluidas en inventario/hash/locks.
- Auditoría ampliada con `before_snapshot_json` y `after_snapshot_json` utilizables e inmutables.
- Suite Odoo ampliada con grafo Camila completo, blockers aislados, colisiones por dominio, rollback con estado real por fase, transient, tampering, snapshots, idempotencia y planes same/inverse.

Evidencia de corrección: RED de contratos por plan/snapshots ausentes; GREEN final `Ran 7 tests ... OK`; compilación, parseo, primitivas prohibidas, whitespace y `git diff --check` pasan. Docker sigue sin daemon, por lo que instalación, suite Odoo y concurrencia real multitransacción requieren revalidación independiente y no se declaran pasadas.

## Corrección tras re-review — 2026-07-20

Sin modificar producción, se reforzó la suite Odoo en los cuatro puntos pendientes:

- El contexto RPC falsificado se ejecuta con `base.user_admin` en un entorno real `su=False`, manteniendo la expectativa de `AccessError`.
- Dos pruebas concurrentes abren cursores/entornos separados y ejecutan confirmaciones same/inverse en threads sincronizados. Comprueban contención efectiva, terminación acotada, una única auditoría y el resultado idempotente o el rechazo del perdedor inverso. El fixture confirmado se elimina de forma determinista en `finally`.
- El blocker contable crea una fila real `res.partner.bank` sobre el origen y demuestra que `action_preview()` falla; el blocker de identidades duplicadas queda aislado en otro fixture.
- El rollback por fase comprueba también restauración del `street` del maestro y de un follower real, junto con usuario, estudiante, lead, categoría, adjunto, origen y ausencia de auditoría.

TDD/evidencia: el nuevo contrato falló primero (`7 passed, 1 failed`) por ausencia de los escenarios y después pasó `8/8`. `compileall`, whitespace, escaneo de primitivas prohibidas en producción y `git diff --check` pasan. Docker continúa sin daemon, así que las pruebas Odoo —incluidas las multitransacción— no tienen resultado runtime local y deben ejecutarse en Validación. No se hizo commit, push ni PR.

## Blocker contable funcional tras tercera revisión — 2026-07-20

Se añadió un caso Odoo aislado que crea mediante ORM un asiento real `account.move` borrador, ligado al partner origen y a un diario general existente de la compañía (con fallback determinista si el runtime no trae uno). El test comprueba `state == "draft"`, el `partner_id` exacto y que `action_preview()` eleva `ValidationError` identificando `account.move.commercial_partner_id` o `account.move.partner_id`. No existen cuenta bancaria ni otros blockers en ese método, de modo que la causa queda aislada; TransactionCase revierte automáticamente asiento y diario al terminar.

Evidencia TDD: el contrato ampliado falló primero (`7 passed, 1 failed`) porque faltaba el caso contable y quedó GREEN `8/8` después de añadirlo. `compileall` y el escaneo de primitivas prohibidas en producción pasan. No se modificó producción ni se hizo commit, push o PR; la ejecución runtime Odoo sigue pendiente por ausencia del daemon Docker.

## Corrección de fallos runtime — 2026-07-20

El runtime recuperado expuso y permitió corregir los errores de la primera Validación:

- El inventario ya no intenta buscar ni ordenar registros en modelos abstractos sin campo `id`; el criterio estrecho conserva las vistas SQL consultables.
- La M2M inversa `res.partner.category.partner_ids` se reconoce como la misma relación aprobada de categorías, sin abrir otras M2M desconocidas.
- Los fixtures académicos aportan `min_count` positivo y las ventas se crean como singletons para respetar el override instalado.
- Los usuarios sintéticos evitan membresías de canal incidentales no incluidas en el escenario; las tarjetas creadas incondicionalmente por otro addon se eliminan solo durante la preparación del fixture Camila. La política productiva sigue bloqueando canales/tarjetas no autorizados.
- La prueba concurrente reproduce la frontera real de petición mediante `odoo.service.model.retrying`. Same e inverse sufren contención/`SerializationFailure` real y terminan respectivamente en idempotencia o rechazo funcional, con una sola auditoría.

TDD del defecto principal: RED enfocado `0 failed, 1 error` por `Invalid field 'id' on model 'hr.employee.base'`; GREEN enfocado `0 failed, 0 errors` de 1 test. La suite completa posterior pasó dos veces: upgrade `0/0 de 31` en 7.96 s y 15.325 queries; instalación limpia `0/0 de 31` en 9.92 s y 15.324 queries. Contrato estático `8/8`, compilación, scan de seguridad y `git diff --check` pasan.

Se eliminaron las dos bases aisladas, el filestore y el overlay. Los servicios canónicos continúan `Up` y sus hashes no cambiaron. Esta sección y `verification.json` son evidencia de Implementación; un validador independiente debe repetir el gate final. No hubo commit, push ni PR.
