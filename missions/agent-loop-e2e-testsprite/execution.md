# Execution — agent-loop-e2e-testsprite

## Contexto de arranque

Rama `feat/agent-loop-e2e-testsprite` creada desde `Dev_iRG` actualizada
(`git fetch origin Dev_iRG` → `git merge --ff-only`), base `41628848d`.

TestSprite MCP quedó registrado en scope `user` en la sesión previa
(`claude mcp add TestSprite --scope user -e API_KEY=... -- npx -y @testsprite/testsprite-mcp@latest`),
estado `✔ Connected` en `claude mcp list`.

## Análisis previo

Corrección registrada: el primer análisis del ciclo se hizo sin haber leído
`AGENTS.md` y calificó de "drift" el formato `plan.md` / `verification.json`. Es
falso: `AGENTS.md` es la política canónica del repo y ese formato es el suyo. Las
77 misiones lo cumplen. También se retiró la afirmación de que la fase de Review
estaba muerta: es fase, no artefacto `02b-review.md`.

Lo que sí se sostuvo tras leer `AGENTS.md`:

- `AGENTS.md:84` ya exige E2E "cuando cruza componentes".
- `grep -ril "testsprite\|playwright\|selenium\|tour" AGENTS.md missions/*/verification.json`
  → **0 resultados**. El gate está en la política y ninguna misión lo satisface.
- Los checks reales del histórico son `unit_tests` (18), `xml_parse` (14),
  `python_compile` (13), `odoo_module_update` (12). Todos headless.

## Decisiones

| Decisión | Elección | Motivo |
| --- | --- | --- |
| Gate | Bloqueante con reintentos | Coherente con el trato que `AGENTS.md` da a cualquier `fail` de validación |
| Disparo | Por scope del diff | Evita quemar ejecución cloud en misiones de cron y cálculo |
| Posición | Tras el resto de checks | No gastar E2E sobre código que no compila |
| `PROJECT.md` | Capa de hechos subordinada | No crear una tercera política que compita con `AGENTS.md` |

## Tareas

### T1 — `PROJECT.md`

Creado. Stack, layout (18 dirs de addons, 167 módulos `irg_`, 6375 manifiestos),
runtime local, comandos canónicos, convenciones, Git y zonas sensibles.

Se registra explícitamente que **no existe lint canónico**: ningún
`verification.json` del histórico contiene un comando de lint real, así que el
archivo prohíbe inventarse uno.

### T2 — Capa E2E en `AGENTS.md`

Sección "Capa E2E" insertada entre "Runtime local, worktrees y limpieza" y
"Seguridad". Define disparo por scope, posición tras el resto de checks, gate
`E2E PASS` / `E2E FAIL`, escalado al usuario tras dos fallos por la misma causa, y
los límites de exposición a la nube de TestSprite.

### T3 — Agente `e2e-tester`

Creado en `.claude/agents/e2e-tester.md`. Modelo `sonnet` (routing de validación).
Herramientas acotadas: `Read, Bash, Grep, Glob` más los 7 tools MCP de TestSprite.
Bloque de prohibiciones explícito: nada de beta ni producción, `projectPath` nunca
en raíz ni en `etc/`, `docker/`, `docker-compose*.yml`, sin credenciales reales.

### T4 — Verificación

Ver `verification.json`.

## Limitación conocida

**El gate no se ha ejercido de extremo a extremo.** El servidor MCP TestSprite se
registró después del arranque de esta sesión, de modo que sus tools
(`mcp__TestSprite__*`) no están cargados y no se ha podido correr ni siquiera
`testsprite_check_account_info`. Lo verificado es la coherencia documental y de
configuración, no el funcionamiento real del gate. El check `e2e_testsprite` va
`skipped` con esa justificación.

La primera misión con scope web que se ejecute tras reiniciar la sesión es la
prueba real de esta capa.
