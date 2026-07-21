# Independent review — IRG Partner Safe Merge

## Scope

Reviewed the approved plan and micro-spec, the task brief/report, project policy and Odoo knowledge, and every source/configuration/test file under `addons-extra/extrairg/irg_partner_safe_merge`. Generated `__pycache__` files were also inventoried; they are ignored build artifacts, not deliverable source. Production code was not modified.

## Findings

### [P1] The closed-world inventory misses every direct Many2many reference except partner categories

`_relation_inventory()` discovers only stored `many2one` fields related to `res.partner`, then reference/polymorphic fields, and finally appends `category_id` manually (`wizard/partner_safe_merge_wizard.py:408-460`). It never queries `ir.model.fields` for `ttype = 'many2many'` and never inspects their relation tables. Consequently, any installed direct M2M containing the source outside `res.partner.category_id` is neither transferred nor blocked; the source can be archived while that relation still points to it. This violates the closed allowlist rule that every non-classified reference with source rows must block, as well as the requirement to inventory/lock M2M relations. Add generic M2M discovery for blocking and an explicit static exception only for the approved category union (including relation-row locking/hash state).

### [P1] The preview hash does not bind the scalar decisions that are actually executed, and RPC context can forge generated state

The hash contains master/source IDs, scalar snapshots and relation inventory, but omits the conflict-line choices (`wizard/partner_safe_merge_wizard.py:770-777`). Confirmation validates the mutable lines before acquiring locks (`wizard/partner_safe_merge_wizard.py:189-207`) and later executes their then-current values (`wizard/partner_safe_merge_wizard.py:816-823`). The UI even collects choices after `action_preview`, so the displayed “final preview” cannot represent the effective scalar action plan. In addition, generated wizard and conflict metadata are protected only by caller-supplied context flags (`wizard/partner_safe_merge_wizard.py:103-121` and `1029-1041`), which an administrator can include in an RPC context to write `preview_hash`, `preview_ready`, or line metadata. Rebuild and validate decisions under the lock, include them in the effective-plan hash, and do not use forgeable context alone as the integrity boundary.

### [P1] User/student “exact coherence” is not enforced

The coherence checks run only when `student.user_id` is set (`wizard/partner_safe_merge_wizard.py:378-406`). A source can therefore contain one `res.users` and one `op.student` with an empty `user_id`, or a master user plus a source student not linked to that user, and pass preflight. Confirmation then moves users and students independently (`wizard/partner_safe_merge_wizard.py:827-840`), preserving or creating a graph that was never proven coherent. The approved contract requires exact coherence before transfer. Validate all presence combinations explicitly and include the student-to-user link in the preview snapshot/hash.

### [P1] The required allowlisted e-learning wizard transfer is unreachable

`op.admission.elearning.wizard.partner_id` is declared in the transfer allowlist (`wizard/partner_safe_merge_wizard.py:13-30`), but the generic inventory discards every transient model before classification (`wizard/partner_safe_merge_wizard.py:418-421`). Since `op.admission.elearning.wizard` is a `TransientModel`, its rows are never inventoried, locked or transferred. This is a direct mismatch with the approved transfer policy. Handle this allowlisted transient explicitly, or amend the approved micro-spec before implementation.

### [P1] Mandatory behavioral tests are missing or do not prove the claimed guarantees

The Camila-equivalent test creates only four leads, one user and one student (`tests/test_partner_safe_merge.py:117-150`); it creates/asserts no sale orders, admissions, subscription schedule, messages, activities or attachments, despite those being mandatory. The blocker test leaves the bank reference in place before checking duplicate users (`tests/test_partner_safe_merge.py:151-171`), so that second assertion can pass solely because of the bank and does not prove the duplicate-user guard. The rollback loop creates plain partner copies with no phase-specific user/student/FK/follower graph and asserts only source marker/audit state (`tests/test_partner_safe_merge.py:210-227`); moreover, `assertRaises` is nested inside the savepoint, so it suppresses the exception before the savepoint context can roll back, and no mutated master/relation value is checked. The “concurrency” coverage only asserts sorted IDs and performs no competing transaction (`tests/test_partner_safe_merge.py:198-208`, `229-237`). Add isolated tests for every mandatory blocker and mutation phase, a complete Camila graph, real rollback assertions, and concurrent same/inverse confirmations. The Odoo suite has not been executed, so none of these runtime guarantees currently has passing evidence.

### [P2] Business-collision preflight is not complete for the named domains

The only semantic collision checks are slide-channel membership and Stripe subscription (`wizard/partner_safe_merge_wizard.py:611-640`). All other transfers rely on physical unique indexes (`wizard/partner_safe_merge_wizard.py:641-702`). There is no explicit collision policy for admissions, gradebooks, sales or payment schedules as required, and no tests establishing the intended business keys. A duplicate that is semantically invalid but not backed by a database unique index will be transferred. Define the approved business keys/conditions for the named models, lock both source and target rows, and test each blocker.

## Verification notes

- No standard partner `_merge()`, `cr.commit()`, or SQL `DELETE FROM` was found in production source.
- The admin checks, source marker restrictions, unique audit origin, immutable audit methods, direct-partner polymorphic filtering, computed/related reclassification, deterministic partner lock ordering, and follower subtype union are present in code.
- `git diff --check` passed. The addon and mission files remain untracked; no commit, push or PR was performed.
- Docker/Odoo integration was unavailable to the implementer and remains unpassed; static parsing/compilation cannot establish installability or runtime ORM behavior.

CHANGES_REQUESTED

## Nota de corrección del implementador — 2026-07-20

Esta nota no sustituye el dictamen anterior. Se implementaron correcciones para cada P1/P2: M2M closed-world con lock de relación de categorías; decisiones y enlace usuario-estudiante en hash bajo lock; guardas internas `su` + contexto; coherencia exacta; transient e-learning explícito; snapshots antes/después; políticas de colisión de admisiones/gradebooks/ventas/schedules; y suite Odoo ampliada/aislada. Los contratos estáticos pasan 7/7 y `compileall`, parseo, whitespace y `git diff --check` pasan.

La suite Odoo y concurrencia multitransacción aún no pudieron ejecutarse porque Docker continúa sin daemon. El árbol queda listo para re-review de código, pero no para aprobar el gate de Validación runtime.

## Re-review independiente — 2026-07-20

Se inspeccionaron las correcciones reales de producción y tests, sin confiar en la nota del implementador. Quedan resueltos en código los hallazgos previos sobre inventario M2M cerrado, decisiones y enlaces usuario-estudiante dentro del hash, guardas internas `su` + contexto, coherencia exacta, transferencia explícita del transient, políticas de colisión de los cuatro dominios y snapshots de auditoría antes/después. Los snapshots se construyen antes de mutar y después de archivar (`wizard/partner_safe_merge_wizard.py:1065-1141`), incluyen escalares/categorías/usuarios/estudiantes/enlaces (`wizard/partner_safe_merge_wizard.py:1238-1260`) y sus campos permanecen bajo la inmutabilidad general de auditoría (`models/merge_audit.py:25-47`).

### [P1] La suite Odoo ampliada contiene un test RPC que necesariamente falla bajo `TransactionCase`

La clase usa directamente `self.env`/`cls.env` heredado de `TransactionCase` (`tests/test_partner_safe_merge.py:9-15`), cuyo entorno estándar en Odoo 16 se crea con `SUPERUSER_ID`. El test de contexto falsificado invoca `wizard.with_context(_irg_safe_merge_wizard_service=True).write(...)` esperando `AccessError` (`tests/test_partner_safe_merge.py:435-440`), pero la guarda de producción autoriza exactamente `env.su` más ese contexto (`wizard/partner_safe_merge_wizard.py:134-149`). Por tanto, en ese test `internal` es verdadero y la escritura se acepta. La suite no puede estar GREEN tal como está; el test debe ejecutar la RPC simulada con un administrador real no-`su` (por ejemplo `base.user_admin`) y conservar separada la prueba del servicio interno `su`.

### [P1] Siguen faltando las pruebas obligatorias de concurrencia y de bloqueo funcional de pagos/contabilidad

La supuesta cobertura concurrente solo compara el orden calculado de IDs en dos wizards (`tests/test_partner_safe_merge.py:508-514`); no abre dos cursores/transacciones ni ejecuta confirmaciones same/inverse contendiendo por los locks. La otra prueba es idempotencia secuencial dentro de una sola transacción (`tests/test_partner_safe_merge.py:392-399`). Esto no cubre la confirmación inversa concurrente exigida por la micro-spec. Asimismo, `test_payment_and_accounting_relations_are_explicit_block_policies` solo llama directamente a `_classify_relation()` (`tests/test_partner_safe_merge.py:468-484`): no crea ninguna fila de pago/contabilidad enlazada al origen ni demuestra que `action_preview()` la descubra y bloquee. Añadir pruebas de integración reales para ambos contratos; no basta un token, una clasificación aislada ni verificar el orden de una lista.

### [P2] El test de rollback aún no comprueba la restauración del cambio escalar

El fixture provoca una copia de `street` desde el origen (`tests/test_partner_safe_merge.py:342-378`) y ahora sitúa correctamente el savepoint dentro de `assertRaises`, pero las aserciones posteriores solo revisan origen, usuario, estudiante, lead, categoría, adjunto y auditoría (`tests/test_partner_safe_merge.py:379-390`). No se comprueba que el `street` del maestro haya vuelto a su valor anterior, por lo que la fase `scalars` sigue sin demostrar rollback del dato que realmente mutó. Guardar y afirmar el valor escalar preexistente en cada iteración.

### Comprobaciones ejecutadas

- Contrato estático local: `Ran 7 tests ... OK`; confirma sintaxis/parseo y tokens, no comportamiento Odoo.
- `git diff --check`: pass.
- Búsqueda de `_merge`, `cr.commit` y `DELETE FROM` en producción: sin coincidencias.
- `docker version`: cliente disponible, daemon ausente en `npipe:////./pipe/docker_engine`; no fue posible ejecutar instalación ni suite Odoo.
- No se modificó código productivo y no se hizo commit, push ni PR.

CHANGES_REQUESTED

## Nota de tercera corrección del implementador — 2026-07-20

Esta nota no altera el dictamen del revisor. Se aplicaron únicamente los refuerzos de test solicitados, sin cambios en producción: entorno `base.user_admin` no-`su` para tampering RPC; blocker real mediante `res.partner.bank`; rollback del escalar del maestro y follower; y confirmaciones same/inverse con dos cursores, dos entornos, threads, eventos, contención, timeout, verificación de auditoría/marker y cleanup.

El contrato dirigido tuvo RED (`7 passed, 1 failed`) antes de editar la suite y GREEN final (`Ran 8 tests ... OK`). Compilación, whitespace, escaneo de primitivas prohibidas en producción y `git diff --check` pasan. Docker sigue sin daemon, por lo que no se atribuye GREEN a la suite Odoo ni a la concurrencia runtime. El árbol se devuelve a tercera revisión; no hubo commit, push ni PR.

## Tercera revisión independiente — 2026-07-20

### Correcciones verificadas

- El test de manipulación RPC ya usa un entorno real de `base.user_admin` y demuestra explícitamente `admin_env.su == False` antes de esperar `AccessError` (`tests/test_partner_safe_merge.py:624-633`). Ya no hereda el modo superusuario del `TransactionCase`.
- Los escenarios concurrentes usan dos threads, dos cursores y dos entornos Odoo independientes, con commit del fixture, contención coordinada mediante eventos, timeout SQL, joins acotados y cleanup en una transacción separada. Las aserciones distinguen correctamente la idempotencia same-direction de la invalidación inverse-direction y verifican una única auditoría y el marker final (`tests/test_partner_safe_merge.py:97-256`, `:709-725`). El uso de `registry.cursor()` y `api.Environment(cr, uid, context)` es compatible con Odoo 16.
- La prueba de rollback conserva y comprueba el valor previo de `master.street`, además de verificar la restauración del follower y del resto del grafo tras cada fallo inyectado (`tests/test_partner_safe_merge.py:505-579`).

### Hallazgo bloqueante restante

**[P1] Falta todavía un blocker funcional real de pago/contabilidad.**

El único registro financiero creado para probar el bloqueo en `action_preview()` es `res.partner.bank` (`tests/test_partner_safe_merge.py:445-451`). Una cuenta bancaria del contacto no es un asiento, línea contable, pago ni transacción. Para `account.move`, `account.move.line`, `account.payment`, `payment.transaction` y `payment.token`, la suite solo llama directamente a `_classify_relation()` y comprueba el literal `"block"` (`tests/test_partner_safe_merge.py:661-677`); eso no ejercita el inventario relacional real ni demuestra que `action_preview()` encuentre y bloquee un registro existente asociado al origen.

Debe añadirse al menos un caso que cree un registro real de pago o contabilidad ligado al partner origen —por ejemplo, un `account.move` válido— y afirme que `wizard.action_preview()` eleva `ValidationError`. El caso de banco puede conservarse, pero no sustituye este requisito explícito.

### Comprobaciones ejecutadas

- Contrato estático local: `Ran 8 tests ... OK`.
- `git diff --check`: pass.
- Escaneo de `_merge`, `cr.commit` y `DELETE FROM` en código productivo: sin coincidencias.
- Revisión del último cambio: limitado a tests y evidencia; no se observan regresiones nuevas en producción.
- Docker sigue sin daemon disponible, por lo que no fue posible ejecutar la suite Odoo runtime ni atribuirle GREEN.
- No se modificó código productivo y no se hizo commit, push ni PR.

CHANGES_REQUESTED

## Nota de corrección del blocker contable — 2026-07-20

Esta nota no sustituye el dictamen independiente. Se añadió exclusivamente el test solicitado: crea un `account.move` real de tipo `entry`, en borrador, con diario general y `partner_id` igual al origen; después exige que `action_preview()` falle con `ValidationError` cuyo texto identifica `account.move.commercial_partner_id` o `account.move.partner_id`. El método está aislado del caso bancario y de cualquier otro blocker, y TransactionCase proporciona rollback del fixture.

El contrato dirigido tuvo RED (`7 passed, 1 failed`) antes del test y GREEN final (`Ran 8 tests ... OK`). `compileall` y el escaneo de primitivas prohibidas en producción pasan. No hubo cambios de producción, commit, push ni PR; Docker continúa sin daemon y no se atribuye GREEN runtime a la suite Odoo. El árbol se devuelve para sign-off final del revisor.

## Sign-off final independiente — 2026-07-20

El único P1 pendiente queda resuelto por `test_source_account_move_blocks_preview` (`tests/test_partner_safe_merge.py:453-485`): el caso crea mediante ORM un `account.move` real, de tipo `entry`, en estado `draft`, con diario general y `partner_id` igual al contacto origen. Las aserciones previas sobre `state` y `partner_id` confirman que el fixture contable existe y apunta al partner correcto antes de invocar el flujo público `action_preview()`.

El fixture es plausible para Odoo 16: `account.move`, `account.journal`, `move_type`, `journal_id`, `partner_id`, `date` y `ref` son APIs/campos válidos; un asiento vacío puede existir en borrador y no se intenta publicarlo. El módulo dispone de la dependencia contable a través de `isep_sale_subscription_extension`, que depende expresamente de `account`. La búsqueda reutiliza un diario general de la compañía y el fallback crea uno con los campos mínimos válidos. `TransactionCase` revierte el registro al finalizar el test.

La causa tampoco admite un falso positivo ajeno: `assertRaisesRegex` exige que el `ValidationError` incluya `account.move.commercial_partner_id` o `account.move.partner_id`. Es exactamente el formato `model.field` emitido por `_relation_inventory()` al encontrar una relación bloqueada. Se admite `commercial_partner_id` porque Odoo lo calcula y almacena desde `partner_id`, y el inventario ordena los metadatos por nombre; ambas rutas pertenecen expresamente al blocklist contable. Una validación de identidad, banco u otra relación no satisface ese regex.

El cambio final está aislado a la suite y su contrato/evidencia. No se observan modificaciones productivas ni regresiones nuevas: los archivos de producción conservan el estado revisado previamente y el escaneo dirigido sigue sin `._merge(`, `cr.commit(` ni `DELETE FROM`. El contrato estático termina `Ran 8 tests ... OK`, `compileall -q` pasa y `git diff --check` no informa errores. Docker continúa sin daemon, por lo que este sign-off de Review no atribuye ejecución runtime a la suite Odoo; ese límite permanece consignado para Validación.

No se hizo commit, push ni PR.

APPROVED

## Re-review de código de la versión runtime — 2026-07-20

Alcance revisado: únicamente el delta funcional posterior al sign-off anterior en producción y tests. No hay hallazgos bloqueantes.

- `_can_search_persistent_rows()` aplica el guard mínimo correcto (`"id" in model._fields`) antes de búsquedas genéricas en inventarios Many2one, Many2many, Reference y polimórficos (`wizard/partner_safe_merge_wizard.py:476-533`, `:573-685`). Omite `hr.employee.base`, que es abstracto, `_auto=False` y carece de `id`, pero no omite por `_auto=False`: las vistas SQL y cualquier modelo persistente ORM con `id` siguen siendo buscados y sometidos a clasificación closed-world. Los modelos concretos que heredan un abstracto conservan su propia metadata, por lo que sus referencias no quedan ocultas. No se identifica ningún modelo persistente desconocido que pueda ser saltado por este criterio.
- El inventario de categorías conserva ahora las filas relacionales separadas por rol `source`/`master`, además de `ids` y `target_ids` (`wizard/partner_safe_merge_wizard.py:573-628`). Esto mantiene estable y sensible al sentido el payload firmado, sigue bloqueando todas las M2M no autorizadas y no amplía la allowlist. El bloqueo y la unión posteriores continúan operando sobre ambos partners con orden canónico.
- Los ajustes de tests corrigen fixtures, no relajan contratos: `min_count=1` satisface la validación real de admisiones; las órdenes se crean individualmente para respetar el override singleton instalado; las tarjetas sintéticas creadas como efecto lateral se eliminan solo dentro del fixture que prueba el grafo transferible. Los escenarios de bloqueo permanecen separados.
- La prueba de modelo abstracto reproduce el crash concreto y exige que el preview continúe. Las confirmaciones concurrentes usan cursores independientes y `odoo.service.model.retrying`, que representa el retry transaccional de Odoo 16 ante serialización, conservando las aserciones same/inverse de una auditoría, marker final y perdedor inválido (`tests/test_partner_safe_merge.py:99-266`, `:308-314`, `:773-789`). Cleanup y timeouts permanecen acotados.

Comprobaciones independientes: contrato estático `Ran 8 tests ... OK`; `compileall -q` pass; sin whitespace inválido; sin `._merge(`, `cr.commit(` ni `DELETE FROM` en producción; `git diff --check` sin errores. No se editó producción y no se hizo commit, push ni PR.

APPROVED
