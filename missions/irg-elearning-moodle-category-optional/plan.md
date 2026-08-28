# Plan — irg_elearning_moodle_category_optional

## Objetivo

Permitir que un curso de eLearning (`slide.channel`) se guarde y se abra en el sitio web sin seleccionar una categoría de Moodle, mediante un módulo puente nuevo y sin modificar `odoo_moodle_connector`.

## Contexto y conocimiento consultado

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`: los módulos nuevos se ubican en `addons-extra/extrairg/`, usan prefijo `irg_` y herencia estándar.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_elearning_url_slide.md`: los cambios de `website_slides` deben validarse en una base limpia con `docker-compose.local.yml`.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_partner_gender.md`: `irg_partner_gender` depende funcionalmente del conector Moodle para otros ajustes, por lo que no se desinstala ni se modifica el conector.

## Alcance

- Crear `addons-extra/extrairg/irg_elearning_moodle_category_optional`.
- Depender de `odoo_moodle_connector` para garantizar el orden de carga.
- Heredar `slide.channel` y redefinir `category_id` con `required=False`, conservando comodelo, etiqueta y semántica.
- Heredar la vista de formulario del conector y declarar explícitamente `required="0"` para el campo.
- Añadir pruebas que demuestren que el metadato ya no es obligatorio y que puede crearse/editarse un curso sin categoría Moodle.
- Mantener intacta la lógica de sincronización Moodle del conector.

## Fuera de alcance

- Crear o sincronizar categorías Moodle.
- Modificar credenciales, endpoints o comportamiento de sincronización.
- Corregir datos históricos o instalar/desinstalar módulos en producción.
- Hacer commit, push, PR o despliegue.

## Criterios de aceptación

1. `env['slide.channel']._fields['category_id'].required` es `False` con el módulo instalado.
2. La vista efectiva no obliga a completar `category_id`.
3. Es posible crear y actualizar un `slide.channel` con `category_id=False` en una base de prueba sin credenciales Moodle.
4. El campo sigue apuntando a `moodle.categories` y mantiene la etiqueta `Course Category`.
5. No se modifica ningún archivo de `odoo_moodle_connector` ni de `irg_partner_gender`.

## Estrategia TDD y validación

1. Crear primero el arnés del módulo y una prueba Odoo enfocada.
2. Ejecutar la prueba antes del override y conservar evidencia RED.
3. Implementar el cambio mínimo en modelo y vista.
4. Ejecutar GREEN en una base dedicada mediante `docker-compose.local.yml` y un overlay que monte este worktree.
5. Ejecutar checks de sintaxis Python, parseo XML, estructura del manifest y revisión de diff.
6. Un revisor distinto examina código/pruebas/configuración funcional.
7. Un validador distinto repite los checks y emite `verification.json`.
8. Como el diff toca `views/*.xml`, ejecutar el gate `e2e_testsprite` después de los demás checks; si el runtime o la herramienta no están disponibles, registrar `skipped` con evidencia y justificación objetiva conforme a la política vigente de `Dev_iRG`.

Si Docker o el runtime Odoo local no están disponibles, el codificador debe registrar la causa objetiva antes de implementar y ejecutar las comprobaciones estáticas posibles; el validador marcará cualquier prueba no ejecutada como `skipped` con justificación explícita.

## Riesgos y mitigaciones

- **Orden de definición del campo:** dependencia explícita del conector y módulo separado.
- **Vista todavía obligatoria:** override Python más herencia XML explícita.
- **Sincronización con credenciales activas:** no se cambia el flujo del conector; la prueba usa una base aislada sin credenciales.
- **Regresión en el conector:** se comprueba que relación y etiqueta permanecen iguales y que no hay cambios en el módulo original.

## Clasificación y roles

- Nivel de misión: `full`, por cambiar comportamiento de runtime.
- Tier requerido: `complex`, por superar cinco archivos funcionales contando el scaffolding y las pruebas, aunque la lógica sea acotada.
- Orquestador/documentador: agente principal.
- Codificador TDD: agente independiente asignado.
- Revisor de código: agente distinto del codificador.
- Validador: agente distinto del codificador.
- Security Advisor: no aplica; no cambia autenticación, permisos, secretos, despliegue, concurrencia, datos ni borrado histórico.

## Artefactos esperados

- `plan.md`
- `execution.md`
- `verification.json`
- `artifacts/tdd-red.txt`
- `artifacts/tdd-green.txt`
- `artifacts/code-review.txt`
- `artifacts/static-checks.txt`
- `artifacts/e2e-testsprite.txt`
- `CHANGELOG.md`
- micro-spec aprobada en `doc/micro-specs/2026-08-18-irg_elearning_moodle_category_optional.md`

## Base y entorno

- Worktree: `C:/tmp/irg-elearning-moodle-category-optional`
- Rama: `codex/irg-elearning-moodle-category-optional`
- Commit base inicial: `41628848dbda4e0537eada3a5e67beed68e98a9c`
- Base de publicación actualizada: `4e57a337a` (`origin/Dev_iRG` tras fast-forward).
- Runtime previsto: `docker-compose.local.yml` del checkout principal con overlay de montaje al worktree.
