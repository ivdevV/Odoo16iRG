# Review 2 — irg-practice-request-online-types

Review 1 (agente distinto del coder): REVIEW FAIL.

BLOQUEANTE-1: JS hacía `option.hidden = isOnline && !allowed`, lo que des-ocultaba la opción legacy id=2.
BLOQUEANTE-2: reasignar `typeSelect.value` sin `change` dejaba requisitos/horario desalineados.

Corrección: solo `hidden = true` cuando online y no permitido; `dispatchEvent(new Event('change'))` tras reasignar.

Review 2: REVIEW OK.
Validación independiente: `verification.json` `passed`. `e2e_testsprite` skipped (TestSprite MCP no conectado).
