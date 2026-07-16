# Changelog — improve-agents-md

- Reorganiza `AGENTS.md` como política canónica y ejecutable con un ciclo de vida
  explícito: Plan, Implementación/TDD, Review, Validación, Documentación y
  Publicación autorizada.
- Define misiones proporcionales, routing por capacidad, gates correctivos,
  validación independiente, runtime Odoo aislado y limpieza verificable.
- Separa las autorizaciones de commit, push y PR, y conserva el OK explícito y de
  un solo uso para publicar en `Dev_iRG`.
- Añade un checker estructural con 41 pruebas de regresión, más 2 pruebas offline
  que demuestran el aislamiento y cleanup del inspector de publicación.
- Exige una revalidación del árbol final después de Documentación y antes de
  cualquier publicación autorizada.

## Validación

- `43` tests pasaron sin fallos (`41` de política y `2` del inspector remoto).
- Los `15` contratos ejecutables de política pasaron.
- El ejemplo de `verification.json`, el scan de placeholders/contradicciones y
  `git diff --check` pasaron.
- `verification.json` quedó en estado `passed`; el runtime Odoo se omitió con
  justificación por tratarse exclusivamente de documentación y checker.

## Concern de integración

En la observación remota final, `Dev_iRG` estaba en `581bd1d5`; esta rama aún parte
de una base anterior. Antes de integrar debe rebasarse sobre la base remota actual
y repetirse la validación completa.
