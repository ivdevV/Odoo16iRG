# Enrutamiento curso/asignatura Moodle en la libreta

## Objetivo

Corregir la sincronización para distinguir el mapa de curso Moodle del mapa
de asignaturas/actividades. El lote selecciona primero un curso Moodle por
modalidad y edición; solo después se resuelven las asignaturas y sus Activity
IDs dentro de ese curso.

## Alcance y arquitectura

- Crear el addon puente nuevo `irg_gradebook_moodle_routing`, dependiente de
  `irg_gradebook_moodle_wizard`, sin modificar addons existentes.
- Añadir `irg.gradebook.moodle.course.map` para la relación
  `op.course -> curso Moodle`.
- Derivar del nombre Moodle la modalidad autoritativa: nombres que contienen
  `(ONLINE` son online; los demás son HomeClass. Derivar asimismo el año de
  una etiqueta como `(ONLINE 2026)`.
- Extender `irg.gradebook.moodle.map` con el curso Moodle padre.
- Resolver el mapa en el wizard por `gradebook_student.batch_id.code`:
  `HC` selecciona HomeClass y `ONL` selecciona online. Para online se prioriza
  el año del lote y se usa el mapa online sin año como fallback inequívoco.
- Filtrar los mapas de asignatura por el curso Moodle ya resuelto antes de
  llamar al comportamiento heredado.
- Importar los tres CSV de forma idempotente y en dos niveles:
  - `mapeo cursos homeclass.csv` autoriza los cursos HomeClass;
  - `mapeo cursos online.csv` constituye el inventario de cursos online;
  - `Mapeo asignaturas.csv` aporta las relaciones curso/asignatura/Activity ID
    y los nombres que identifican modalidad y edición.
- No importar como HomeClass una pareja ausente del CSV HomeClass. En
  particular, el Moodle Course ID `36` queda excluido mientras solo esté
  autorizado el `35` para el curso Odoo `1`.
- Añadir vistas separadas para mapas de curso y mapas de asignatura.

## Criterios de aceptación

1. Un lote cuyo código contiene `HC` usa exclusivamente un curso Moodle cuyo
   nombre no contiene `(ONLINE`.
2. Un lote cuyo código contiene `ONL` usa exclusivamente un curso Moodle cuyo
   nombre contiene `(ONLINE`.
3. Un código ambiguo (`HC` y `ONL`) o sin modalidad reconocida bloquea la
   carga con un mensaje explícito.
4. Para un lote online de 2026 se prioriza `(ONLINE 2026)`; un mapa genérico
   `(ONLINE)` solo actúa como fallback si la selección es inequívoca.
5. Las asignaturas se consultan únicamente dentro del mapa de curso elegido.
6. El importador es idempotente, valida IDs positivos, no borra datos
   históricos y deja fuera parejas no autorizadas.
7. El listado de cursos muestra curso Odoo, ID/nombre Moodle, modalidad,
   edición y estado; el listado de asignaturas muestra su curso padre.
8. Los permisos de lectura son para usuarios internos y la administración de
   mapas queda restringida a administradores, igual que en el addon base.

## TDD y validación

1. RED: pruebas de clasificación del nombre, selección por lote, aislamiento
   de asignaturas y parsing/importación de los tres CSV.
2. GREEN: implementación mínima del addon puente.
3. Review independiente de código y datos funcionales.
4. Validación independiente con `docker-compose.local.yml`, incluyendo
   instalación/upgrade, tests Odoo, import real en transacción reversible,
   sintaxis Python, XML, CSV, `git diff --check` y estado Git.
5. Documentación posterior a Review y Validación.

## Riesgos y controles

- **Datos persistentes:** el importador hace upsert y vincula mapas, sin
  eliminar registros. Las pruebas reales se ejecutan con rollback o en base de
  test.
- **Ambigüedad de edición:** se bloquea antes de consultar Moodle; nunca se
  elige arbitrariamente.
- **Datos antiguos sin curso padre:** permanecen intactos pero el wizard nuevo
  no los consume hasta que un import autorizado los vincula.
- **Código de lote inconsistente:** se rechaza con error funcional explícito.
- **Credenciales:** no se leen ni registran en el importador ni en las pruebas
  de routing.

## Tier, roles y publicación

- Misión `full`, tier `complex`: addon nuevo, modelos persistentes, datos,
  vistas, integración con wizard y más de cinco archivos.
- Plan: orquestador.
- Security Advisor: agente independiente antes de implementar.
- Implementación/TDD: codificador.
- Review: agente distinto del codificador.
- Validación: agente independiente que no edita producción.
- Documentación: posterior a Review y Validación aprobadas.
- No se hará commit, push ni PR sin una autorización nueva y explícita para
  cada acción. La autorización anterior ya fue consumida por la entrega previa.

## Knowledge consultada

- `.agents/workflows/odoo16_codebase_knowledge.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diploma_gradebook_beta_course_detection.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diploma_gradebook_presential_detection.md`
- `missions/irg-gradebook-moodle-wizard/plan.md`
