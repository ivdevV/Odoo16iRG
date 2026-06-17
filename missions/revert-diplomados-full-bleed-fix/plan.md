# Mission: revert-diplomados-full-bleed-fix

## Objetivo
Revertir el ultimo cambio aplicado al modulo `irg_generacion_diplomados` porque rompio completamente el diploma generado.

## Alcance
- Restaurar `addons-extra/extrairg/irg_generacion_diplomados/reports/diplomado_templates.xml` al estado previo al commit `f5d92b31`.
- Eliminar de la historia efectiva los artefactos de la mision rota `missions/diplomados-full-bleed-fix/` mediante un commit de revert.
- No tocar otros modulos ni cambios ajenos del worktree.

## Clasificacion de complejidad
`trivial`: revert localizado de un commit conocido, sin logica nueva.

## Criterios de validacion
- `xmllint` sobre XML de reportes de diplomados.
- Actualizacion del modulo con `docker-compose.local.yml`.

## Resultado esperado
El diploma vuelve al layout estable anterior al cambio de `web.basic_layout`/`position: fixed`.
