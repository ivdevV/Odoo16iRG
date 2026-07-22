# Wizard Moodle para la libreta de calificaciones

## Alcance

Implementar el plan aprobado `docs/superpowers/plans/2026-07-21-irg-gradebook-moodle-wizard.md` mediante un módulo nuevo `irg_gradebook_moodle_wizard`, sin modificar módulos existentes. El módulo añade mapeo de actividades Moodle, lectura puntual de grade items, un wizard editable por alumno y upsert tipado en `app.gradebook.result`.

## Criterios de aceptación

1. El botón solo aparece en la libreta individual de un alumno.
2. El matching usa `md_id`, email y nombre normalizado, por ese orden.
3. Los IDs importados coinciden tanto con `item.id` como con `item.cmid`.
4. Las notas se convierten a la escala de la libreta y se promedian por asignatura y tipo.
5. Quiz crea/actualiza `exam`; tarea crea/actualiza `assignment`.
6. La clave `(gradebook_subject_id, is_moodle, survey_type)` evita duplicados funcionales.
7. El wizard permite editar la nota antes de aplicar.
8. No se modifica `irg.moodle.subject.map`, su cron ni los computes base de `isep_gradebook`, salvo extensión defensiva si el test demuestra que `compute_name` lo requiere.

## Tier, roles y gates

- Nivel de misión: `full`.
- Tier: `complex`, por superar cinco archivos, cruzar módulos, API externa, datos persistentes, vistas, ACL, tests y runtime Odoo.
- Plan: orquestador.
- Implementación/TDD: codificador, con RED antes de producción conforme a la autorización del usuario para adelantar Task 7.
- Review: agente independiente del codificador.
- Validación: agente independiente, sin editar producción.
- Documentación: posterior a Review y Validación satisfactorias.
- Publicación: push y PR únicamente dentro de la autorización expresa contenida en la petición de aplicar íntegramente el plan.

## Pruebas y runtime

- Suite `TransactionCase` del plan, ampliada solo si un RED revela requisitos reales del modelo base.
- Instalación, upgrade y tests con `docker-compose.local.yml` y un overlay que monte este worktree en `/mnt/extra-addons`.
- Base indicada por el plan: `test_irg_db`.
- Smoke real del WS para determinar `id` frente a `cmid`, si las credenciales y datos existentes lo permiten.
- Smoke manual/UI del flujo completo y comprobación de no duplicación.
- Checks estáticos de Python, XML, CSV, diff y alcance Git.
- Limpieza de fixtures/containers efímeros y confirmación de que el servicio compartido continúa montando el checkout principal.

## Knowledge consultada

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_auto_close.md`
- `.agents/workflows/odoo16_codebase_knowledge.md`
- Plan aprobado indicado arriba.

## Fuera de alcance

Se mantiene íntegramente la sección «Fuera de alcance» del plan aprobado.
