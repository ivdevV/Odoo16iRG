# Registro de ejecución

## 2026-09-07 — Plan

- Usuario confirmó comprobación de campos afectados y relaciones, bloqueo sin
  excepciones de administrador, flujo en dos etapas y cobertura de pendientes.
- Revisados HEAD/status Git, módulo base, wizard, ACL, vistas, pruebas y knowledge.
- Base: 928c2974ba94acfa4bb6e8730c14426f9071fc6e, rama Dev_iRG.
- Hay modificaciones y archivos ajenos previos; no se han tocado.
- Creado plan.md antes de cualquier cambio funcional. Sin implementación,
  instalación, modificación de datos, commit, push o PR.
- Plan completo pendiente de aprobación del usuario; Security Advisor y gates
  funcionales se ejecutarán al comenzar la implementación.

## Implementación autorizada

- Usuario: «lo apruebo implementalo». Worktree codex/irg-enrollment-modification-guard creado desde 928c2974.
- Runtime de pruebas: compose local con overlay scratch/irg-enrollment-guard/compose.guard.json mediante run --rm --no-deps; el servicio web compartido sigue montando el checkout original.
- Decisión: conservar cambios sin commit; permisos de publicación separados.

- Baseline: 19 tests del addon base, 0 fallos/0 errores; una prueba de modalidad omitida por ausencia del campo Studio en la BD plantilla. Se cubrirá modalidad expresamente con fixture local.

## Preflight y gate de seguridad

- Security Advisor: NO inicial por fantasmas de líneas; plan enmendado y segunda revisión YES antes de producción. Evidencia artifacts/security-review.txt.
- Capacidad complex: implementador gpt-6-astra/high seleccionado explícitamente.
- Tareas 2–4 comparten modelo/snapshot/fence: se ejecutan con un codificador y una Review sobre la versión funcional final, como exige AGENTS.md.
- Secuencia 2→3: snapshot protegido alimenta comparación; sin contradicción.
- Secuencia 3→4: acciones usan fence común; ampliar archivo sale_order_line según security.
- Tareas 1/5/6: preparación → checks independientes → documentación; sin revisión documental extra.
- Regla aplicada: AGENTS prevalece sobre commits y reviews por subtarea de la skill; no hay autorización de commit.
- Regla aplicada: compose run aislado evita cambiar el servicio compartido; al cierre se verificará identidad/montajes intactos y se limpiarán solo recursos creados aquí.

- Preparada BD independiente odoo16irg_guard_validation clonada de test_irg_db para validador, sin instalar guard ni modificar fuente.

## Implementación/TDD

Leídos plan enmendado, Security Advisor YES, knowledge de matrícula y skill TDD. RED inicial usa modelo base real, fixtures legacy anteriores a instalar guard y campo Studio manual solo en BD desechable. No código de producción nuevo antes del RED.

- RED baseline: `prepare_red.py` (Odoo shell sobre base desechable), confirma sobreescritura C→B y deja fixtures históricas. Primer intento fixture falló por idioma es_ES no disponible; corregido a env.user.lang y repetido. No se había escrito código de producción.
- RED suite antes de modelos guard: 34 tests, 28 assertions failed y 10 errors por campos todavía inexistentes. Señales funcionales: state API mutable, origen falso aceptado, lote y pago externos sobrescritos.
- Primera implementación: 53 tests, 0 assertions failed, 4 errors. Tres son ausencia real de ACL académica para Finanzas; Security Advisor aprueba lectura académica privada limitada (artifacts/security-finance.txt) antes de cambiar privilegios. Un error fixture copy de alumno por birth_date vacío corregido usando create explícito.
- Pruebas de dos conexiones: enrollment/payment/insert/unlink/modality/move propagan SerializationFailure; doble aprobación y denegación muestran bloqueo real pg_stat_activity y solo una transición tras retry. Cleanup script restores sus fixtures. Falta ampliación retry PDF y fence inverso antes review final.

- GREEN final funcional: `green-full-3.txt`: 60 tests, 0 failed, 0 errors. Incluye 19 tests base y 41 guard (19 heredados base para comprobar fixture + 22 específicos); contador puro aprobado, reglas y compañía rechazadas, datos académicos no divulgados, modalidad Studio en varias líneas sin skips.
- GREEN concurrente final: `concurrency-final.txt`: 10 escenarios con dos conexiones; doble aprobación/denegación/retry PDF verifican una transición o un adjunto, un escritor concurrente espera en fence adquirido por aprobación, serializa y tras retry conserva su edición y bloquea Finanzas. Cleanup incluido restaura fixtures afectadas.
- Runner concurrente empaquetado como `tests/test_enrollment_guard_concurrency.py`, invocado explícitamente desde Odoo shell para disponer de conexiones y commits reales fuera de TransactionCase. Los commits existen únicamente en scripts de fixtures/tests y nunca en modelos de producción.
- Comprobación AST/sintaxis y manifest correcta (8 archivos Python), whitespace normalizado, alcance solo addon nuevo y misión. No addons existentes editados, no commit/push/PR. Versión funcional congelada para Review independiente; detalles reproducibles en artifacts/implementation-report.txt.

## Cierre solicitado por usuario

- Usuario: «finaliza ya». Review interrumpida por límite de uso del agente, sin veredicto.
- Pendiente candidato fence defaults ORM, ver artifacts/review-interrupted.txt.
- Validación independiente no ejecutada y documentación final no iniciada (gates pendientes).
- verification.json status failed: no declarar misión validada ni publicar.
- Dos bases y filestores temporales eliminados. Servicio original verificado intacto.
- Código conservado sin commit/push/PR en worktree codex/irg-enrollment-modification-guard.

## Reapertura por Review — defaults y fence

Review `code-review-retry.txt` solicita P1: pedido por ir.default no cercado; P2: defaults de solicitud contextual no neutralizados. Skill receiving-code-review aplicado; requisito contrastado con create y reproducido antes del fix. BD test anterior ya eliminada; por autorización del orquestador se creó `odoo16irg_guard_fix` desde fuente y se repitió instalación base + fixtures históricas + instalación guard anterior.

RED: alta line_section por ir.default no serializa (`review-fix-red-concurrency.txt`); contexto agrega change_payment (`review-fix-red-context.txt`); default persistido agrega visto académico (`review-fix-red-saved-defaults.txt`). Corrección: resolver y fijar order_id antes fence; neutralizar todos defaults protegidos y fijar vals técnicos antes super.create. Detalle `artifacts/code-review-fix.txt`.

GREEN corregido: 62 tests 0fail/error (`review-fix-green-full.txt`), 11 escenarios concurrentes PASS con cleanup (`review-fix-green-concurrency.txt`), AST/whitespace 8 archivos PASS. Sin cambios ajenos ni publicación. Versión funcional congelada para nueva Review y Validación independiente. Bases desechables pendientes de cleanup de orquestación, runtime web original intacto.

## Revisión y validación final — 2026-09-07

- Rereview independiente: APPROVED en `artifacts/code-review-rereview.txt`.
- Validación fresca tras el fix: 62 tests, 0 fallos y 0 errores en `odoo16irg_guard_fix` (`artifacts/independent-validation.log`).
- Concurrencia fresca: 11 escenarios PASS, incluido `ir.default` y cleanup del runner (`artifacts/independent-concurrency.log`).
- Documentación creada después de Review y Validación. El diff no toca vistas, QWeb, assets, portal, controladores ni plantillas; `e2e_testsprite` queda skipped con justificación de scope.
