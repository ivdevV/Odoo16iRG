# Execution — excluir encuestas sin calificación

## Estado inicial

- Misión creada después de leer `AGENTS.md`, `SPECIFICATIONS.md`, el workflow del repositorio y la knowledge base relevante.
- Checkout: rama `Dev_iRG`, basada en `a6d4b0d31`.
- El checkout ya tenía cambios no relacionados; quedan fuera del alcance y no se modificarán.
- No hay autorización de commit, push, PR ni despliegue.

## Causa y alcance confirmados

- `irg_exam_second_attempt` incluye respuestas `survey` en la sincronización y las clasifica como `exam` salvo que sean `assignment`.
- Una encuesta `survey` con `scoring_type=no_scoring` puede terminar asociada a una asignatura y aportar `0,00`.
- El fix se limitará a excluir esa combinación, conservando asignaciones con `no_scoring` y encuestas puntuables.

## Línea base

- `docker compose version` → no disponible: `docker: 'compose' is not a docker command`.
- `docker-compose version` → binario no instalado.
- `docker ps` → no se puede conectar al daemon Docker en `/var/run/docker.sock`.
- El repositorio contiene `docker-compose.yml`, pero no `docker-compose.local.yml`; la política del repositorio exige el runtime local para pruebas Odoo.
- La prueba Odoo de línea base queda pendiente de runtime; no se marcará como pasada por inferencia.

## Implementación y pruebas

1. Se añadió primero `test_no_scoring_survey_is_not_synced_to_gradebook`.
2. Como el runtime Odoo estaba bloqueado, el arnés equivalente cargó la versión de `HEAD` y la versión actual: la versión previa falló el contrato y la actual pasó.
3. Se implementó el filtro común en `send_result`, sincronización automática, agrupación de intentos y sincronización pendiente.
4. Se añadió `test_no_scoring_assignment_still_syncs_to_gradebook` para proteger el caso especial de asignaciones.
5. Se subió el módulo a `16.0.1.0.1` y se creó la documentación de módulo.
6. El contrato aislado ampliado pasó para encuesta no puntuable, encuesta puntuable, asignación y sincronización pendiente.

## Validación pendiente por infraestructura

- La suite `TransactionCase` de Odoo no pudo arrancar porque no hay módulo Python `odoo`, `docker-compose`, plugin `docker compose` ni daemon Docker en este host.
- El repositorio no contiene `docker-compose.local.yml`, que es el runtime exigido por `AGENTS.md`.
- La integración de instalación/actualización del módulo queda pendiente de ejecutar en un runtime Odoo local autorizado.

## Revisión y publicación

- Revisión independiente inicial: `passed`; sin observaciones de seguridad ni lógica.
- El ajuste posterior conserva el retorno `None` del método heredado y actualiza su evidencia.
- La lectura autorizada de Odoo Producción confirma que `get_gradebook` está desinstalado; no se modifica ese módulo ajeno ni se añade como dependencia.
- Segunda revisión de `irg-developer`: `passed` estáticamente; confirmó la exclusión, la compatibilidad del retorno `None` y las tres categorías. Bloqueo Odoo documentado por falta de runtime.
- Commit/push a `origin/Dev_iRG` autorizados y pendientes de ejecutar; no se desplegará en Producción desde esta misión.
