# Security Advisor — revisión previa

## Alcance revisado

La misión crea exclusivamente el addon puente
`irg_gradebook_moodle_routing`, dependiente de
`irg_gradebook_moodle_wizard`. Añade datos de routing persistentes, extiende
el mapa de asignatura existente y filtra el mapa antes de que el wizard haga
una llamada al API de Moodle. No introduce controladores HTTP, endpoints
públicos, secretos nuevos, cambios de autenticación ni borrado de datos.

## Controles aprobados y obligatorios en la implementación

- Conservar la autorización server-side ya existente en los tres puntos de
  entrada del wizard (`action_open_moodle_sync_wizard`, carga y aplicación).
  La visibilidad de botones o vistas no será el único control.
- El nuevo modelo de mapa de curso tendrá ACL explícitas: lectura para
  `base.group_user` y crear/escribir/borrar solo para `base.group_system`,
  igual que el mapa base. Las vistas y las acciones no deben ampliar esos
  permisos.
- El `Many2one` padre nuevo en `irg.gradebook.moodle.map` debe poder quedar
  vacío para conservar los registros históricos durante el upgrade; el wizard
  ha de buscar solo mapas activos vinculados al mapa de curso elegido. Nunca
  debe reutilizar un mapa huérfano ni seleccionar por ID de Moodle sin esa
  relación autorizada.
- La selección debe rechazar, antes del acceso a Moodle, modalidad ausente o
  ambigua y múltiples candidatos de la misma prioridad. Para online, el
  fallback sin edición solo es válido si también es único. Los tests deben
  cubrir explícitamente estos rechazos y el aislamiento de asignaturas entre
  cursos.
- Persistir y validar IDs de Moodle como enteros positivos, y usar
  restricciones de unicidad o comprobaciones equivalentes que hagan visible
  cualquier duplicidad de mapa de curso. No se aceptarán valores CSV que se
  conviertan de forma implícita, valores no finitos ni pares curso/asignatura
  fuera de los CSV autorizadores.
- El importador hará upsert únicamente de las claves presentes en los tres
  CSV, sin `unlink`, sin desactivar ni reasignar masivamente registros
  históricos. La relación HomeClass ausente (en particular Odoo 1/Moodle 36)
  permanece sin mapa padre y por tanto fuera del routing nuevo. La ejecución
  real será en transacción reversible o base de pruebas; no se incluirán
  credenciales, rutas sensibles ni contenidos de CSV con datos personales en
  logs o artefactos.
- Los comandos de validación previstos usan `docker-compose.local.yml` con
  overlay del worktree y deben restaurar el servicio compartido. El importador
  se ejecutará dentro de Odoo con una ruta de archivo controlada, no desde
  valores proporcionados por clientes web.

## Integridad, contratos y sintaxis

El contrato mantiene la semántica de upsert de resultados y no cambia los
permisos para escribir notas: el filtro solo reduce el conjunto de mapas que
el wizard puede usar. Los cursos y asignaturas se resuelven por datos internos
autorizados, y la respuesta Moodle continúa pasando por la validación del
servicio base. El uso de ORM y dominios parametrizados evita SQL construido
con CSV; cualquier SQL de bloqueo heredado permanece fuera de este cambio.

La modalidad se deriva de nombres de Moodle solo como dato de routing y no de
la entrada de un usuario. Debe normalizarse de forma determinista y tratar el
nombre nulo o una edición no reconocible como no seleccionable, no como
HomeClass por defecto. La importación idempotente y la ausencia de borrados
evitan pérdida de datos; los registros antiguos sin padre no se consumen.

No hay objeciones bloqueantes al diseño, siempre que los controles anteriores
formen parte del addon y de sus pruebas RED/GREEN antes de llamar al API
Moodle.

[YES] Reason: El diseño limita el routing a mapas internos autorizados, preserva la autorización server-side y los datos históricos, y no amplía APIs, ACL ni acceso a credenciales.
