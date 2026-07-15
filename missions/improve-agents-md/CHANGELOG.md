# Changelog — improve-agents-md

- Reorganiza `AGENTS.md` como política canónica y ejecutable con un ciclo de vida
  explícito: Plan, Implementación/TDD, Review, Validación, Documentación y
  Publicación autorizada.
- Define misiones proporcionales, routing por capacidad, gates correctivos,
  validación independiente, runtime Odoo aislado y limpieza verificable.
- Separa las autorizaciones de commit, push y PR, y conserva el OK explícito y de
  un solo uso para publicar en `Dev_iRG`.
- Añade un checker estructural con 37 pruebas de regresión y evidencias concisas
  de alcance, política y publicación.

## Validación

- `37` tests pasaron sin fallos.
- Los `14` contratos ejecutables de política pasaron.
- El ejemplo de `verification.json`, el scan de placeholders/contradicciones y
  `git diff --check` pasaron.
- `verification.json` quedó en estado `passed`; el runtime Odoo se omitió con
  justificación por tratarse exclusivamente de documentación y checker.

## Concern de integración

La rama está un commit por detrás de `origin/Dev_iRG`. Antes de integrar debe
rebasarse sobre la base remota actual y repetirse la validación completa.
