# Mission plan — fix-gradebook-homeclass-edition-fallback

## Clasificación

- Tipo: bugfix de comportamiento.
- Misión: `full`.
- Tier: `complex`, porque el addon puente requiere más de cinco archivos y
  cambia la resolución integrada entre routing, mapas y wizard, aunque el
  comportamiento sea acotado.
- Security Advisor: no aplica; no hay autenticación nueva, secretos,
  concurrencia, migración destructiva, despliegue ni borrado.

## Base de conocimiento

- `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_moodle_course_activity_routing.md`
- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`

La corrección conserva la jerarquía curso Odoo → curso Moodle → asignatura /
Activity IDs y extiende por herencia, sin editar addons publicados.

## Criterios de aceptación

1. Varios HomeClass activos no bloquean `action_load_moodle_data`.
2. La edición del año inicial del lote tiene prioridad.
3. Los otros HomeClass se consultan como respaldo por asignatura.
4. Nunca se mezclan notas de dos ediciones.
5. Activity IDs se resuelven solo dentro del curso padre.
6. Online no cambia.
7. La edición HomeClass se detecta desde periodos académicos y admite override.

## Roles y gates

- Plan/orquestación/documentación: agente raíz.
- Implementación/TDD: codificador delegado.
- Review de código: revisor independiente.
- Validación: validador independiente distinto del codificador.
- Publicación: fuera de alcance hasta autorización explícita nueva.

## Pruebas

- RED/GREEN dirigido del addon nuevo.
- Regresión de routing, mapping admin y addon nuevo.
- Upgrade Odoo 16 mediante `docker-compose.local.yml` y overlay del worktree.
- `compileall`, parse XML, `git diff --check` y limpieza del runtime.

## Artefactos

- `execution.md`
- `verification.json`
- `artifacts/red-tests.txt`
- `artifacts/green-tests.txt`
- `artifacts/review.txt`
- `artifacts/validation-tests.txt`
- `CHANGELOG.md`

No se hará commit, push, PR, despliegue ni importación real sin autorización.
