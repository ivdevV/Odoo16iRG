# Especificación de seguridad — `fix-auto-enroll-cron`

Fecha de aprobación del diseño: 2026-07-13

## Alcance

Esta especificación modifica exclusivamente cuatro puntos del plan fuente para resolver el
rechazo del Security Advisor. El resto de T0.1–T5 permanece sin cambios.

Decisión funcional previa: las admisiones con `modality='manual'` deben entrar en
auto-enroll. El cron buscará todas las admisiones `done` con `batch_id`, sin filtrar por
modalidad.

## S1 — Guardarraíl transaccional del 30%

El cron conservará el aislamiento mediante savepoint por admisión para que una admisión que
falle no impida procesar las demás. Además, el run completo estará protegido por un
savepoint exterior.

Antes y después de procesar se comparará el campo `active` de todas las memberships cuyos
pares `(partner_id, batch_id)` correspondan a las admisiones objetivo. Este alcance incluye
filas históricas sin `admission_id`. Solo cuentan memberships cuyo estado cambie durante el
run:

- `activated_count`: `False -> True`.
- Una membership nueva creada activa también suma en `activated_count`.
- `archived_count`: `True -> False`.
- `initial_active_count`: número total de memberships activas incluidas en el snapshot
  anterior al run.

Tras el fallo detectado por la validación T4.2 y la aprobación explícita del usuario del
2026-07-13, el ratio será `archived_count / initial_active_count`. Si
`initial_active_count == 0`, el ratio será cero. Las activaciones se mantienen como contador
de observabilidad, pero no forman parte del denominador. Así, archivar una membership entre
un conjunto amplio no se interpreta como una desmatriculación masiva solo porque sea el único
cambio del run.
Si el ratio es estrictamente mayor que `0.30`, el cron debe:

1. Emitir un `WARNING` con activadas, archivadas, activas iniciales y porcentaje.
2. Lanzar una excepción fuera de los savepoints individuales.
3. Revertir todas las altas, reactivaciones, archivados y actualizaciones del run.
4. Dejar que Odoo registre el traceback y haga rollback. Odoo 16 actualizará después
   `lastcall/nextcall`; no se promete un estado persistente nativo de “fallido” ni reintento
   inmediato.

El umbral se aplica al run completo, no por admisión. Exactamente 30% no aborta.

## S2 — Unicidad concurrente por alumno, canal y lote

El micro-módulo añadirá un índice único parcial sobre `slide_channel_partner` para filas
`active=True` y `batch_id IS NOT NULL`, con clave:

- `partner_id`.
- `channel_id`.
- `batch_id`.

Así cron y botón no pueden confirmar dos memberships activas para el mismo alumno, canal y
lote aunque partan de snapshots concurrentes. Las filas archivadas y las memberships de
lotes distintos seguirán permitidas.

Antes de crear el índice, la instalación comprobará que no existen duplicados activos con
esa clave y abortará sin modificar datos si encuentra alguno. El diagnóstico read-only de
beta del 2026-07-13 encontró 0 grupos duplicados activos por esa clave y 213 grupos
históricos con duplicados al contar activas y archivadas; estos últimos no se tocarán.

El conflicto exacto del índice se aislará con savepoint en `auto_enroll_student()` y en la
reconciliación del canal clonado. Si otra transacción ya confirmó la misma membership, se
registrará el conflicto concurrente y se continuará; cualquier otra `IntegrityError` se
propagará.

Todas las búsquedas de memberships realizadas por auto-enroll y por la sincronización del
clon incluirán el `batch_id` actual. Cuando coexistan una fila activa y filas archivadas de
la misma clave, se seleccionará primero la activa; solo si no existe activa se reutilizará la
archivada más antigua. Nunca se trasladará una membership de otro lote cambiándole sus
metadatos.

Las búsquedas que deban reutilizar archivadas usarán explícitamente
`with_context(active_test=False)`; el domain por sí solo no desactiva el filtro implícito de
Odoo sobre el campo `active`.

Homeclass y Online pueden coexistir: normalmente usan el canal original y su clon Online,
respectivamente. El índice también permite el mismo canal si el `batch_id` es distinto. La
beta contiene 92 alumnos activos simultáneamente en un canal Homeclass y su clon Online.

## S3 — Trigger nativo bajo demanda

Los hooks `create/write/unlink` de `op.subject.to.batch` llamarán a un helper del
micro-módulo `irg_auto_enroll_cron_robust` únicamente cuando cambien `date_from`, `date_to`
o `subject_id`.

El helper resolverá el cron por su XML ID y llamará directamente a `_trigger()`, sin bloquear
ni modificar la fila de `ir_cron` y sin mantener estado auxiliar.

Se aceptan varias filas temporales `ir.cron.trigger` cuando una operación modifica muchas
líneas. Odoo selecciona el `ir.cron` una sola vez aunque existan varias filas vencidas y las
elimina conjuntamente al finalizar; no equivalen a múltiples ejecuciones del job.

Bajo `REPEATABLE READ`, un trigger confirmado después del snapshot de una ejecución en curso
no es visible para su `DELETE` final y permanece para provocar la siguiente ejecución. Un
cambio confirmado antes del snapshot sí es visible para el run actual y puede limpiarse.

No se modificará el código base de `ir.cron` ni se creará una cola adicional.

## S4 — Fallback histórico aislado por lote

El helper compartido de precedencia primero buscará la membership del padre para la
admisión actual, como hace el código vigente. Si no existe una completada, el fallback
histórico exigirá simultáneamente:

- `partner_id` del alumno actual.
- `op_subject_id` de la asignatura padre.
- `batch_id` del lote actual.
- `completed=True`.

El fallback incluirá memberships activas y archivadas y no exigirá `admission_id`. Una
membership completada en otro lote nunca podrá desbloquear la asignatura hija.

## Pruebas obligatorias añadidas al plan

- El guardarraíl deja pasar exactamente 30% de las activas iniciales, aborta con más de 30%
  y prueba que el rollback restaura todos los estados.
- Un único archivado dentro de un alcance con suficientes memberships activas se aplica sin
  que las activaciones del mismo run tengan que compensarlo.
- Dos transacciones concurrentes cron/botón sobre la misma admisión no incrementan el número
  de memberships.
- Un cambio Homeclass→Online conserva la membership Homeclass y crea/reutiliza la del canal
  Online clonado sin conflicto.
- Dos lotes que comparten canal no reutilizan ni reasignan la membership del otro lote.
- Una activa actual se prioriza sobre una archivada histórica más antigua.
- Cada hook relevante crea al menos un trigger pendiente.
- Un cambio confirmado durante una ejecución en curso conserva un trigger para otro run.
- El fallback acepta una completada histórica del mismo lote y rechaza una de otro lote.

## Restricciones de entrega

- El backfill de T3.2 será un script one-shot entregado como artefacto, no cargado por ningún
  manifest, hook o data XML y nunca ejecutado en `Base16`.
- No habrá push, despliegue beta ni PR hasta `verification.json: passed` y un OK explícito
  nuevo del usuario.
- No se realizará merge.
