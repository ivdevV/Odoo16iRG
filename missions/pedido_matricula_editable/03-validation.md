# Validación — Misión `pedido_matricula_editable`

**Validator:** ejecución real e independiente de todos los criterios (no se confía en lo
reportado por Coder/Reviewer; todos los comandos de este documento se han corrido
directamente contra el estado actual del working tree en `Dev_iRG`).

**Fecha:** 2026-07-02
**Módulo bajo validación:** `addons-extra/extrairg/irg_pedido_matricula_editable/`

---

## Verificación previa: estado de módulos protegidos

Criterio: `irg_sale_order_extended` e `irg_pedido_matricula_rvoe` NO deben haber sido
modificados.

```
$ git status --short -- addons-extra/vztech/irg_sale_order_extended addons-extra/extrairg/irg_pedido_matricula_rvoe
(sin salida)

$ git diff -- addons-extra/vztech/irg_sale_order_extended addons-extra/extrairg/irg_pedido_matricula_rvoe
(sin salida)
```

**Resultado: PASS.** Ningún archivo de esos dos módulos aparece como modificado ni
tiene diffs frente a HEAD.

---

## Tarea 1 — Scaffold del módulo (manifiesto)

- **C1** — Existen `__init__.py` y `__manifest__.py`:
  ```
  $ test -f "addons-extra/extrairg/irg_pedido_matricula_editable/__init__.py" \
      && test -f "addons-extra/extrairg/irg_pedido_matricula_editable/__manifest__.py" && echo OK
  OK
  ```
  **PASS**

- **C2** — Manifiesto es dict Python válido:
  ```
  $ python3 -c "import ast; ast.literal_eval(open('.../__manifest__.py').read()); print('OK')"
  OK
  ```
  **PASS**

- **C3** — `depends` exactamente `['irg_sale_order_extended']`:
  ```
  $ python3 -c "import ast; d=ast.literal_eval(...); assert d['depends']==['irg_sale_order_extended'], d['depends']; print('OK')"
  OK
  ```
  **PASS**

- **C4** — `data` referencia el XML del reporte:
  ```
  $ python3 -c "import ast; d=ast.literal_eval(...); assert 'reports/registration_order_editable_template.xml' in d['data']; print('OK')"
  OK
  ```
  **PASS**

Contenido verificado del manifiesto (`cat __manifest__.py`):
```python
# -*- coding: utf-8 -*-
{
    'name': 'IRG Pedido de Matrícula (editable)',
    'version': '16.0.1.0.0',
    'summary': 'Añade el reporte editable de Pedido de Matrícula para sale.order',
    'author': 'Antigravity',
    'category': 'Sale',
    'depends': ['irg_sale_order_extended'],
    'data': ['reports/registration_order_editable_template.xml'],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
```
`__init__.py` contiene únicamente `# -*- coding: utf-8 -*-`.

**Tarea 1: PASS (C1, C2, C3, C4 todos PASS).**

---

## Tarea 2 — Copia fiel del template QWeb + acción de reporte

- **D1** — XML sintácticamente válido:
  ```
  $ python3 -c "import xml.etree.ElementTree as ET; ET.parse('.../registration_order_editable_template.xml'); print('OK')"
  OK
  ```
  Verificación adicional con `lxml` y `xmllint --noout`: ambos también OK
  (parsers independientes, mismo resultado).
  **PASS**

- **D2** — Existen los ids propios (`action_report_registration_order_editable`,
  `registration_order_editable_template`):
  ```
  OK
  ```
  **PASS**

- **D3** — Campos clave de la acción correctos (name, model, report_name/report_file,
  binding_model_id, binding_type, paperformat_id):
  ```
  OK
  ```
  **PASS**

- **D4** — Sin branding RVOE (`grep -i rvoe` sin coincidencias):
  ```
  $ ! grep -i "rvoe" ".../registration_order_editable_template.xml" && echo OK
  OK
  ```
  **PASS**

- **D5 (adaptado)** — El criterio original del plan comparaba el cuerpo del
  `<template>` nuevo contra `irg_pedido_matricula_rvoe/reports/registration_order_rvoe_template.xml`.
  Esa comparación quedó obsoleta: la Iteración 5 de `02-progress.md` documenta que el
  RVOE (805 líneas) NO es copia fiel del predeterminado real, y que el archivo en git de
  `irg_sale_order_extended/reports/registration_order_template.xml` (1532 líneas) tampoco
  coincide exactamente con lo que se imprime hoy en producción/beta (está desactualizado
  frente a `ir_ui_view.arch_db`).

  Se adaptó la verificación en dos pasos, ejecutados de forma independiente por este
  Validator (sin confiar en lo reportado por Coder/Reviewer):

  **Paso A — comparación estructural contra el archivo real en disco de
  `irg_sale_order_extended`** (similitud de tags, para confirmar que sigue el mismo
  esqueleto: `web.html_container` > `t-foreach docs` > `web.basic_layout` > 3 páginas):
  ```
  $ wc -l addons-extra/vztech/irg_sale_order_extended/reports/registration_order_template.xml \
          addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml
     1532 .../irg_sale_order_extended/reports/registration_order_template.xml
     1556 .../irg_pedido_matricula_editable/reports/registration_order_editable_template.xml

  $ python3 - <<'PY'
  # SequenceMatcher sobre secuencia de tags (tag, attrs sin id/t-name)
  ...
  orig tag count: 782
  new tag count: 789
  structural similarity ratio: 0.9713558243157224
  num non-equal opcodes: 7
  PY
  ```
  Resultado: 97.1% de similitud estructural. El `diff` textual normalizado (id/t-name
  neutralizados) muestra que las ~7 discrepancias son cambios de **contenido** (texto de
  cláusulas renumeradas 1-24 vs 1-25, "Nombres y Apellidos" -> "Nombre", "e-campus" ->
  "Unimarconi", ajustes de estilo `<table>`, corrección ortográfica "correspndientes" ->
  "correspondientes", etc.), NO cambios estructurales de la plantilla. Esto es consistente
  con lo documentado en la Iteración 5: el archivo en git de `irg_sale_order_extended`
  está desactualizado frente al contenido real en producción.

  **Paso B — verificación independiente contra la fuente de la verdad (BD viva de beta,
  solo lectura)**, repitiendo por cuenta propia (sin depender del reporte del Coder) la
  extracción que documenta la Iteración 5:
  ```
  $ ssh odoobetairg "echo CONEXION_OK"
  CONEXION_OK

  $ ssh odoobetairg "docker ps --format '{{.Names}}' | grep -i pg"
  nat16_pgodoo_latest

  $ ssh odoobetairg "docker exec nat16_pgodoo_latest psql -U odoo -d Base16 -t -A \
      -c \"SELECT arch_db->>'en_US' FROM ir_ui_view WHERE id=5285\"" > live_view_5285.xml
  $ wc -l live_view_5285.xml
     1541 live_view_5285.xml
  ```
  Se extrajo el cuerpo interno del `<t t-name="...">` de la vista viva (1539 líneas) y el
  cuerpo interno del `<template id="registration_order_editable_template">` del módulo
  nuevo (1539 líneas), y se compararon con `diff`:
  ```
  $ diff live_body.xml new_template_body.xml
  (sin salida)
  $ echo "exit code: $?"
  exit code: 0
  ```
  **Resultado: DIFF VACÍO.** El cuerpo del template nuevo es byte-idéntico al contenido
  real de `ir_ui_view.id=5285` en `Base16` (servidor beta), que es la vista que
  actualmente renderiza "Pedido de matrícula" en producción/beta. Esto confirma de forma
  independiente (consulta SQL propia, solo lectura, sin tocar la BD) la afirmación de la
  Iteración 5: el template nuevo SÍ es copia fiel del predeterminado real, aunque no
  coincide byte a byte con el archivo desactualizado en git de `irg_sale_order_extended`.

  **D5 (adaptado): PASS**, verificado por dos vías independientes (similitud estructural
  contra el archivo en disco + diff exacto contra la fuente viva en BD).

**Tarea 2: PASS (D1, D2, D3, D4 PASS; D5 adaptado PASS con evidencia doble).**

---

## Tarea 3 — Integridad del módulo completo

- **E1** — Todo archivo en `data` existe en disco:
  ```
  OK
  ```
  **PASS**

- **E2** — Los `ref` externos apuntan solo a `sale.*` o `irg_sale_order_extended.*`:
  ```
  refs found: ['sale.model_sale_order', 'irg_sale_order_extended.report_registration_order_paperformat']
  OK
  ```
  **PASS**

- **E3** — No hay ids XML duplicados:
  ```
  OK
  ```
  **PASS**

- **E4** — Verificación runtime (Docker), condicional al entorno:
  ```
  $ docker ps
  failed to connect to the docker API at unix:///Users/ivrogo/.docker/run/docker.sock;
  check if the path is correct and if the daemon is running: dial unix
  /Users/ivrogo/.docker/run/docker.sock: connect: no such file or directory
  ```
  **N/A** — Confirmado independientemente que Docker no está disponible en este entorno
  local. Conforme al plan, no bloquea el veredicto; basta con D1-D5 + E1-E3.
  (Nota: existe un servidor beta remoto accesible por SSH con Docker corriendo, usado
  únicamente para la verificación de solo-lectura de D5 arriba; no se ha instalado ni
  actualizado el módulo `irg_pedido_matricula_editable` en ningún entorno runtime, ya que
  el plan no lo exige cuando Docker local no está disponible y no se dispone de una DB de
  pruebas distinta a `Base16` para no arriesgar producción/beta.)

**Tarea 3: PASS (E1, E2, E3 PASS; E4 N/A por ausencia de Docker local, conforme al plan).**

---

## Tarea 4 (opcional) — Doc de conocimiento

- **F1** — La doc menciona el nuevo módulo:
  ```
  $ grep -q "irg_pedido_matricula_editable" ".agents/knowledge/odoo_sale_order_custom_reports.md" && echo OK
  OK
  ```
  **PASS**

- **F2** — La doc menciona el nuevo id de acción:
  ```
  $ grep -q "action_report_registration_order_editable" ".agents/knowledge/odoo_sale_order_custom_reports.md" && echo OK
  OK
  ```
  **PASS**

**Tarea 4: PASS (F1, F2 PASS).**

---

## Resumen por tarea

| Tarea | Criterios | Resultado |
|---|---|---|
| 1 — Scaffold/manifiesto | C1, C2, C3, C4 | PASS |
| 2 — Template + acción XML | D1, D2, D3, D4, D5 (adaptado) | PASS |
| 3 — Integridad | E1, E2, E3 (E4 N/A) | PASS |
| 4 — Doc (opcional) | F1, F2 | PASS |
| Protección módulos base | `irg_sale_order_extended`, `irg_pedido_matricula_rvoe` sin cambios | PASS |

## Nota metodológica sobre D5

El criterio D5 tal como estaba escrito literalmente en `01-plan.md` comparaba el cuerpo
del template nuevo contra `irg_pedido_matricula_rvoe/reports/registration_order_rvoe_template.xml`.
Esa comparación ya no es válida como criterio de "fidelidad al original" porque, según lo
documentado en la Iteración 5 de `02-progress.md` (y confirmado de forma independiente por
este Validator vía consulta SQL de solo lectura al servidor beta), el RVOE no es una copia
fiel del predeterminado real. Se adaptó D5 verificando (a) similitud estructural contra el
archivo real en disco de `irg_sale_order_extended` (97.1%, discrepancias solo de contenido
textual, no estructurales) y (b) diff exacto (vacío) contra la vista viva `ir_ui_view.id=5285`
en `Base16`, que es la fuente de la verdad de lo que se imprime hoy. Ambas verificaciones
fueron ejecutadas directamente por este Validator, no asumidas del reporte del Coder.

---

# PASS global
