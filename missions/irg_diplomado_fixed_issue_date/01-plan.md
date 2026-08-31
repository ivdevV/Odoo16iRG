# irg_diplomado_fixed_issue_date Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Los diplomas de diplomados imprimen siempre «Barcelona, a 26 de Septiembre de {año de generación}».

**Architecture:** Módulo nuevo por herencia `irg_generacion_diplomados_fixed_issue_date` (no se edita `irg_generacion_diplomados`). Un helper `_irg_fixed_issue_date()` en el registro calcula `date(año_actual, 9, 26)`. El wizard fuerza esa fecha en `create`/`write` y la muestra readonly. El registro solo cambia el default; un `issue_date` explícito se respeta para no romper tests ni históricos.

**Tech Stack:** Odoo 16, herencia `_inherit`, ReportLab existente, tests `TransactionCase` en `docker-compose.local.yml`.

---

## Alcance

Forzar `issue_date` a 26 de septiembre del año de generación en el flujo de
diplomados, sin tocar diplomas ya emitidos.

## Clasificación

- Nivel de misión: `full` (cambio de comportamiento del producto).
- Tier: `standard`. El módulo nuevo añade varios archivos de esqueleto, pero
  la lógica es un único helper y dos herencias locales. No hay autenticación,
  migraciones, secretos ni borrado histórico. Security Advisor no aplica.
- E2E TestSprite: `skipped`. El diff no toca vistas XML, QWeb, `static/`,
  portal, `website` ni controladores HTTP.

## Knowledge base consultada

- `.agents/knowledge/odoo_development_modding/artifacts/diplomado_report_layout.md`
  — el PDF oficial es ReportLab; QWeb es secundario.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_course_duration.md`
  — no modificar `irg_generacion_diplomados`; crear módulo por herencia.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_portal_request.md`
  — el portal crea el registro sin `issue_date` y genera el PDF con
  `action_reprint()`.

## Archivos

- Create: `addons-extra/extrairg/irg_generacion_diplomados_fixed_issue_date/__init__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_fixed_issue_date/__manifest__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_fixed_issue_date/models/__init__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_fixed_issue_date/models/diplomado_registry.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_fixed_issue_date/wizard/__init__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_fixed_issue_date/wizard/diplomado_wizard.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_fixed_issue_date/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_fixed_issue_date/tests/test_fixed_issue_date.py`
- Create: `missions/irg_diplomado_fixed_issue_date/00-spec.md`
- Create: `missions/irg_diplomado_fixed_issue_date/01-plan.md`
- Create: `missions/irg_diplomado_fixed_issue_date/execution.md`

## Gotcha de impresión

`irg_generacion_diplomados_website_verify` sustituye `action_print_diplomado`
sin llamar a `super()`. Forzar `issue_date` en `create`/`write` del wizard
cubre esa ruta. El PDF de ReportLab del módulo base sigue leyendo
`self.issue_date` (ya forzado). El de website_verify lee
`registry.issue_date` (copiado del wizard). El portal no pasa `issue_date`;
el default del registro cubre esa ruta.

## Publicación

Destino: `Dev_iRG` primero. Commit, push y PR quedan fuera hasta OK explícito
del usuario. Push a `Dev_iRG` exige un OK nuevo en ese momento.

## TDD

### Task 1: Tests RED

**Files:**
- Create: módulo esqueleto + `tests/test_fixed_issue_date.py`

- [ ] **Step 1: Escribir tests que fallen**

Casos:

1. `_irg_fixed_issue_date()` devuelve 26/09 del año de `context_today`.
2. Wizard `create` con `issue_date='2020-01-01'` acaba en 26/09 del año actual.
3. Wizard `write` no consigue dejar otra fecha.
4. Registro creado **sin** `issue_date` usa 26/09 del año actual.
5. Registro creado **con** `issue_date='2026-06-16'` conserva esa fecha.
6. `action_print_diplomado` guarda 26/09 del año actual en el registro.

- [ ] **Step 2: Ejecutar RED** con overlay de worktree sobre
  `docker-compose.local.yml` e `-i irg_generacion_diplomados_fixed_issue_date`.

### Task 2: Implementación GREEN

- [ ] Helper `_irg_fixed_issue_date` en `irg.diplomado.registry`.
- [ ] Default de `issue_date` del registro = helper.
- [ ] Wizard: default + `readonly=True` + `create`/`write` fuerzan el helper.
- [ ] `auto_install: True` para que Dev lo active al tener el padre instalado.
- [ ] Ejecutar GREEN.

### Task 3: Review, validación, documentación

- [ ] Review independiente (solo código de producto).
- [ ] Validación independiente → `verification.json`.
- [ ] Documentar módulo y entrada de knowledge.
- [ ] E2E `skipped` justificado por scope.
- [ ] No commit ni push sin OK.
