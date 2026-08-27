# Plan — agent-loop-e2e-testsprite

## Alcance

Añadir una capa E2E al ciclo de vida definido en `AGENTS.md`, implementada con
TestSprite MCP, y crear `PROJECT.md` como capa de hechos del proyecto.

No se toca código de producción de ningún módulo Odoo. No se ejecuta TestSprite
contra beta ni producción.

## Motivación

`AGENTS.md:84` ya exige pruebas "de integración o extremo a extremo cuando cruza
componentes". Grep sobre `AGENTS.md` y las 77 `verification.json` existentes
devuelve cero menciones a testsprite, playwright, selenium o tours de Odoo: el
gate está en la política y ninguna misión lo satisface. Además, el peso histórico
de misiones de renderizado y portal (diplomas, layouts, forum visibility, embeds)
es justo lo que `odoo --test-enable` no cubre.

## Tier

`light`. Cambio documental y de configuración de agentes, sin lógica de producto,
sin runtime, sin datos, sin secretos. Artefactos: `plan.md`, `execution.md`,
`verification.json`.

## Decisiones de diseño (tomadas con el usuario)

1. **Gate bloqueante con reintentos.** `E2E FAIL` reabre Implementación igual que
   cualquier `fail` de validación. Sin `E2E PASS` no hay publicación.
2. **Disparo por scope del diff.** La capa solo corre si el diff toca superficie
   web. En caso contrario el check se registra `skipped` con justificación, según
   el contrato de verificación de `AGENTS.md`.
3. **`PROJECT.md`** recoge stack, comandos canónicos y zonas sensibles. Es capa de
   hechos, subordinada a `AGENTS.md` en proceso; no compite con ella.

## Tareas

### T1 — `PROJECT.md`

Crear `PROJECT.md` en la raíz con: stack, layout de addons, comandos canónicos de
test/build/lint verificados contra `docker-compose.local.yml` y las
`verification.json` existentes, convenciones y zonas sensibles.

Criterio de aceptación: el archivo existe, declara `AGENTS.md` como política
superior, y todo comando que cite debe aparecer literalmente en alguna
`verification.json` del repo o en `docker-compose.local.yml`.

### T2 — Capa E2E en `AGENTS.md`

Añadir a `AGENTS.md` la definición del gate E2E: criterio de disparo por scope,
protocolo TestSprite, contrato del check en `verification.json` y límites de
seguridad.

Criterio de aceptación: `grep -c "e2e_testsprite" AGENTS.md` devuelve >= 1 y la
sección define disparo, gate y límites.

### T3 — Agente `e2e-tester`

Crear `.claude/agents/e2e-tester.md` con el rol invocable, herramientas acotadas y
el veredicto literal `E2E PASS` / `E2E FAIL`.

Criterio de aceptación: frontmatter válido (`name`, `description`, `model`,
`tools`) y el cuerpo prohíbe explícitamente ejecutar contra beta o producción.

### T4 — Verificación

Emitir `verification.json` con checks reales.

Criterio de aceptación: JSON parseable con `python3 -m json.tool`, todo `skipped`
justificado, `status` coherente con los resultados.

## Riesgos

- **Fuga de código a cloud.** TestSprite sube el `projectPath` a su nube y tunela
  el puerto local. Mitigación: `projectPath` apunta al directorio del módulo de la
  misión, nunca a la raíz del repo (que contiene credenciales de producción en
  `etc/` y compose).
- **Credenciales.** `needLogin` requiere un usuario Odoo. Mitigación: solo usuario
  de la BD local desechable; prohibido beta y producción.
- **Coste y latencia.** Un E2E son minutos. Mitigación: disparo por scope y
  posición posterior al resto de checks.
- **Tamaño del repo.** 6375 manifiestos; un resumen de código a nivel raíz es
  inviable. Mitigación: la misma que la de fuga, acotar `projectPath`.

## Orden

T1 → T2 → T3 → T4. T4 depende de las tres anteriores.
