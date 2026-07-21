# Plan — IRG Partner Safe Merge

## Objetivo

Crear el módulo instalable `irg_partner_safe_merge` para que administradores consoliden exactamente dos contactos personales, mantengan separados sus leads, trasladen de forma atómica las relaciones al contacto maestro y archiven el origen con auditoría.

## Alcance y criterios de aceptación

- Acción contextual administrativa desde `res.partner` para dos contactos activos.
- Recomendación explicable del maestro priorizando suscripciones, ventas confirmadas, pagos, usuario/estudiante, completitud y antigüedad.
- Resolución explícita de campos escalares divergentes.
- Prevalidación de identidad, jerarquía, compañía, usuarios, estudiantes, referencias y restricciones únicas.
- Traslado seguro de claves foráneas, referencias, M2M, chatter, actividades, seguidores y adjuntos; ningún fallback puede borrar relaciones ante conflicto.
- Leads independientes: solo cambia `crm.lead.partner_id`.
- Origen archivado mediante `irg_merged_into_partner_id`; auditoría persistente del resultado.
- Caso Camila: maestro `1373479`, traslado de `res.users(1396)` y `op.student(1180)`, cuatro leads separados y suscripción/pedidos intactos.

## Clasificación

- Misión: `full`.
- Tier: `complex`.
- Justificación: cambio cross-module sobre datos de contactos, CRM, ventas, suscripciones y OpenEduCat; incluye concurrencia, permisos y protección contra pérdida de datos.
- Capacidad: razonamiento alto para implementación y Security Advisor obligatorio; revisor, validador y documentador independientes.

## Arquitectura

- Nuevo addon en `addons-extra/extrairg/irg_partner_safe_merge`; no se modifica ningún módulo existente.
- Modelos persistentes: extensión de `res.partner` y auditoría `irg.partner.safe.merge.audit`.
- Modelos transitorios: asistente `irg.partner.safe.merge.wizard` y líneas de conflictos.
- Servicio interno con allowlist cerrada por `modelo.campo`. Los metadatos solo inventarían referencias para bloquear las no clasificadas; nunca autorizan transferencias dinámicas.
- Seguridad UI y server-side limitada a `base.group_system`.
- Micro-spec aprobada por el usuario: `doc/micro-specs/2026-07-20-irg_partner_safe_merge.md`.

## Fases y responsables

1. Implementación/TDD: subagente codificador; RED antes de producción, GREEN y refactor.
2. Review: subagente distinto; requisitos, calidad y seguridad funcional.
3. Validación: subagente independiente; compose local con overlay del worktree, sin editar producción.
4. Documentación: subagente distinto tras validación pasada.
5. Revalidación final del árbol documentado.
6. Commit/push/PR solo con autorizaciones explícitas independientes.

## Pruebas previstas

- Permisos de administrador en UI y servidor.
- Selección, identidad, jerarquía, compañía y contactos ya fusionados.
- Recomendación por suscripción/venta y traslado de usuario/estudiante.
- Campos vacíos y conflictos elegibles.
- Cuatro leads separados, pedidos, admisiones, suscripción y calendario.
- Chatter, adjuntos, actividades, seguidores y M2M.
- Colisión única: bloqueo y rollback íntegro.
- Revalidación concurrente al confirmar.

## Riesgos y mitigaciones

- Restricciones no detectadas: inventario de FK/índices, allowlist cerrada y abortar ante cualquier `IntegrityError`.
- Dos usuarios o estudiantes: bloqueo previo, nunca elegir automáticamente.
- Cambios tras preview: hash de campos/IDs/plan efectivo; bloqueo determinista de contactos y filas aprobadas, seguido de preflight íntegro al confirmar.
- Compose ausente en el worktree: usar el compose local del checkout principal con overlay de volumen y restauración/cleanup documentados.
- Árbol principal sucio: todo el trabajo permanece en `C:\tmp\Odoo16iRG-irg-partner-safe-merge`.

## Conocimiento consultado

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
- `.agents/knowledge/odoo_development_modding/artifacts/student_partner_delegated_fields.md`
- `.agents/workflows/odoo16_codebase_knowledge.md`

## Enmienda tras Security Advisor

- Primer dictamen: `[NO]`; motivo registrado en `execution.md`.
- ORM es la vía predeterminada. SQL se limita a locks y consultas con identificadores estáticos/seguros; se prohíben `cr.commit()`, `_merge()` estándar y cualquier fallback que elimine relaciones.
- Políticas explícitas: `transferir`, `recalcular`, `conservar`, `unir` o `bloquear`, detalladas en la micro-spec.
- `res.users` y `op.student` se revalidan bajo bloqueo y solo se trasladan si el maestro carece de equivalentes y la coherencia usuario-estudiante es exacta.
- Confirmación idempotente mediante lock, marcador del origen y restricción única de auditoría.
- Auditoría inmutable, origen siempre archivado, maestro activo, sin ciclos ni eliminación del origen.
- Marcador escribible solo por el servicio en entorno `su`; reactivación y eliminación del origen fusionado se bloquean server-side.
- Colisiones solo se unen para categorías y followers con semántica aprobada; cualquier otra colisión bloquea.
- Contabilidad publicada, bancos y relaciones desconocidas bloquean la operación.
- Rollback se prueba con fallos inyectados por fase y RPC manipulado.
- Gradebooks stored-related se recalculan, nunca se escriben directamente; `ir.model.data` del origen se conserva.
