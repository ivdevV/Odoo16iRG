# Changelog — `fix-auto-enroll-cron`

## 2026-07-13

### Cambiado

- El cron `Auto Enroll Students` pasa de frecuencia diaria a horaria y su registro XML usa
  `noupdate="1"` para conservar ajustes administrativos durante upgrades.
- El cron procesa todas las admisiones finalizadas con lote, incluidas las de modalidad
  `manual`, y delega cada una en el mismo entrypoint que el botón `Auto-Asignaturas`.
- Cada admisión se aísla con savepoint y el run registra contadores de procesadas,
  activadas, archivadas y errores.
- El guardarraíl revierte todo el run cuando se archiva más del 30% de las memberships
  activas al inicio; exactamente 30% está permitido.
- La precedencia acepta una finalización histórica sin `admission_id` únicamente para el
  mismo alumno, asignatura padre y lote.
- La sincronización Homeclass/Online y la reutilización de memberships archivadas quedan
  aisladas por lote y priorizan la fila activa.

### Añadido

- Micro-módulo `irg_auto_enroll_cron_robust` con hooks de cambios relevantes de
  `op.subject.to.batch` que llaman al trigger nativo del cron.
- Índice único parcial para impedir dos memberships activas del mismo
  alumno/canal/lote, con preflight no destructivo y eliminación durante uninstall.
- Aislamiento de la colisión concurrente exacta del índice mediante savepoints.
- Suite conductual para cron, botón, triggers, concurrencia, Homeclass→Online,
  guardarraíl, precedencia e idempotencia.
- Informe SQL de gaps y backfill one-shot reversible, no cargados por Odoo y no ejecutados
  en `Base16`.

### Retirado

- Override muerto del cron en `irg_online_clone_access_fix`; los demás overrides muertos
  se conservan y se documentan con comentario, como exige el plan.

### Validación

- Suite robusta: 27/27.
- Regresiones online/clone: 13/13.
- T4.2 manual: archivado, reactivación del mismo ID e idempotencia verificadas.
- Guardarraíl: rollback verificado con 4/10 (40%).
- Estado contractual: `verification.json` en `passed`.

### Pendiente de autorización

- Despliegue y observación T4.3 en beta.
- Commit, push y PR de T5.
