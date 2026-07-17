# Plan de misión: student-payment-status

## Fuente y alcance

- Fuente aprobada: `/Users/ivrogo/Downloads/plan-final.md` y
  `missions/student-payment-status/00-spec.md` del checkout principal.
- Objetivo: crear `addons-extra/extrairg/irg_student_payment_status` sin
  modificar módulos existentes.
- Fuera de alcance: bloqueo automático de campus, reclamación por email e
  integración de cuotas Stripe.

## Decisiones cerradas

- Umbral inicial: `2`, configurable con
  `irg_student_payment.moroso_threshold`.
- Gracia inicial: `15` días, configurable con
  `irg_student_payment.grace_days`.
- Todas las facturas académicas `out_invoice` pesan igual; `partial` cuenta.
- La actividad se dirige a un usuario configurable. Si no se configura,
  se elige de forma determinista un usuario interno activo del grupo
  `openeducat_core.group_op_back_office_admin`, priorizando al administrador.
- El hook `_irg_on_status_change(old_status, new_status)` no ejecuta efectos de
  fase 2 y queda como punto de extensión.

## Tier y capacidad

- Misión completa, tier `complex`: módulo nuevo con más de cinco archivos,
  lógica de negocio, cron, chatter, actividades, vistas y pruebas Odoo.
- Capacidad requerida: máxima capacidad de razonamiento disponible para
  integración y review final; capacidad estándar para implementación guiada.
- No se requiere Security Advisor: no cambia autenticación, concurrencia,
  migraciones, secretos, despliegue ni borra datos históricos.

## Fases y propietarios

1. **Plan — orquestador**: verificar patrones, cerrar defaults y preparar
   worktree/artefactos.
2. **Implementación/TDD — codificador**: crear primero tests RED, capturar la
   evidencia, implementar modelo, datos, cron y vistas, y obtener GREEN.
3. **Review — revisor independiente**: comprobar el plan línea por línea,
   seguridad, alcance, calidad y antipatrones.
4. **Validación — validador independiente**: repetir sintaxis, XML,
   instalación y suite en `docker-compose.local.yml` con overlay del worktree;
   no editar código funcional.
5. **Documentación — documentador**: README, changelog de misión y conocimiento
   reutilizable solo si aparece un patrón nuevo.
6. **Revalidación final — validador**: verificar el árbol documentado y emitir
   `verification.json` final y evidencia.
7. **Publicación — entrega**: no commit, push ni PR sin autorización explícita
   separada del usuario.

## Criterios de aceptación

- Estado almacenado `al_dia`/`atrasado`/`moroso` actualizado por cron y por
  método manual, con fecha solo al cambiar.
- Métricas live de cantidad e importe residual mediante búsquedas `sudo()`.
- Dominio de vencidas reutiliza el dominio académico existente, excluye
  rectificativas y respeta la gracia estricta.
- Transiciones dejan chatter; la entrada a `moroso` crea una única actividad
  pendiente de morosidad para el gestor resuelto.
- Vistas incluyen ribbons, smart button, columna decorada, filtros y agrupado.
- Cron diario activo y parámetros por defecto cargados.
- Quince escenarios funcionales cubiertos mediante tests descubribles.
- Instalación y tests pasan en la base local de prueba sin dejar el servicio
  persistente montado al worktree.

## Riesgos y pruebas

- **Permisos contables**: probar métricas con usuario académico sin acceso a
  contabilidad; limitar `sudo()` a lectura de facturas y creación controlada de
  actividad desde cron.
- **Duplicación de actividades**: buscar actividad pendiente del mismo tipo,
  modelo, registro y resumen antes de crear.
- **Vista/ribbons coexistentes**: ocultar ribbons de pago si el alumno está
  archivado y usar XPaths sobre vistas canónicas.
- **Cutoff**: cubrir fuera de gracia, dentro de gracia y fecha límite estricta.
- **Pagador tercero**: cubrir `irg_student_partner_id` aunque `partner_id` sea
  distinto.

## Comandos previstos

- Compilación Python y parseo XML sobre el módulo.
- Docker Compose base del checkout principal más overlay que monta este
  worktree; ejecución con `run --rm --no-deps` para no recrear el servicio.
- Odoo `-i irg_student_payment_status --test-enable --test-tags
  /irg_student_payment_status --stop-after-init` en `test_irg_db`.
- Inspección final de `git diff`, `git status` y mounts del contenedor
  persistente.
