# Progreso — Misión `pedido_matricula_editable`

## Iteración 1 — Tarea 1: Scaffold del módulo (`__init__.py` + `__manifest__.py`)

**Fecha:** 2026-07-02
**Branch:** `Dev_iRG` (sin commits realizados)

### Qué se hizo

Se creó el directorio del nuevo módulo
`addons-extra/extrairg/irg_pedido_matricula_editable/` con dos archivos:

1. `addons-extra/extrairg/irg_pedido_matricula_editable/__init__.py`
   - Contiene únicamente la cabecera de codificación `# -*- coding: utf-8 -*-`,
     igual que el patrón del módulo hermano
     `addons-extra/extrairg/irg_pedido_matricula_rvoe/__init__.py`.

2. `addons-extra/extrairg/irg_pedido_matricula_editable/__manifest__.py`
   - `name`: `IRG Pedido de Matrícula (editable)`
   - `version`: `16.0.1.0.0`
   - `summary`: `Añade el reporte editable de Pedido de Matrícula para sale.order`
   - `author`: `Antigravity` (consistente con el módulo hermano RVOE)
   - `category`: `Sale`
   - `depends`: `['irg_sale_order_extended']` (dependencia mínima única, SIN
     `isep_openeducat_sale` que sí tiene el hermano RVOE)
   - `data`: `['reports/registration_order_editable_template.xml']` (el archivo
     XML referenciado se crea en la Tarea 2, aún no existe en disco; esto no
     afecta los criterios C1-C4 de esta tarea)
   - `installable`: `True`
   - `auto_install`: `False`
   - `license`: `LGPL-3`

No se tocó ningún otro módulo (`irg_sale_order_extended` e
`irg_pedido_matricula_rvoe` quedan intactos). No se realizaron commits git.

### Verificación de criterios de aceptación (ejecutados por el Coder)

- **C1** (existencia de ambos archivos):
  ```
  $ test -f ".../irg_pedido_matricula_editable/__init__.py" && test -f ".../irg_pedido_matricula_editable/__manifest__.py" && echo OK
  OK
  ```
  Resultado: **PASA**

- **C2** (manifiesto es dict Python válido):
  ```
  $ python3 -c "import ast; ast.literal_eval(open('.../__manifest__.py').read()); print('OK')"
  OK
  ```
  Resultado: **PASA**

- **C3** (`depends` exactamente `['irg_sale_order_extended']`):
  ```
  $ python3 -c "import ast; d=ast.literal_eval(...); assert d['depends']==['irg_sale_order_extended'], d['depends']; print('OK')"
  OK
  ```
  Resultado: **PASA**

- **C4** (`data` referencia el XML del reporte):
  ```
  $ python3 -c "import ast; d=ast.literal_eval(...); assert 'reports/registration_order_editable_template.xml' in d['data']; print('OK')"
  OK
  ```
  Resultado: **PASA**

### Estado de tareas del plan

- [x] Tarea 1 — Scaffold del módulo (`__init__.py` + `__manifest__.py`) — IMPLEMENTADA, criterios C1-C4 ejecutados y en verde por el Coder (pendiente de Review/Validate formal).
- [ ] Tarea 2 — Copia fiel del template QWeb + acción de reporte (XML único) — PENDIENTE. El archivo `reports/registration_order_editable_template.xml` referenciado en el manifiesto todavía no existe.
- [ ] Tarea 3 — Integridad del módulo completo (sin referencias rotas) — PENDIENTE (depende de Tareas 1 y 2).
- [ ] Tarea 4 (opcional) — Actualizar doc de conocimiento — PENDIENTE.

### Notas para la siguiente iteración

La Tarea 2 debe crear
`addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml`
copiando fielmente el cuerpo QWeb de
`addons-extra/extrairg/irg_pedido_matricula_rvoe/reports/registration_order_rvoe_template.xml`,
cambiando únicamente los ids propios (`action_report_registration_order_editable`,
`registration_order_editable_template`) y sin introducir referencias a `rvoe`.

## Iteración 2 — Tarea 2: Copia fiel del template QWeb + acción de reporte (XML único)

**Fecha:** 2026-07-02
**Branch:** `Dev_iRG` (sin commits realizados)

### Qué se hizo

Se creó
`addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml`
(archivo único `<odoo><data>...</data></odoo>`) mediante `cp` literal de
`addons-extra/extrairg/irg_pedido_matricula_rvoe/reports/registration_order_rvoe_template.xml`
seguido de una edición puntual (`Edit`, un solo bloque de reemplazo) que
cambió exclusivamente:

1. El record `ir.actions.report`:
   - `id`: `action_report_registration_order_rvoe` -> `action_report_registration_order_editable`
   - `name`: `Pedido de matrícula RVOE` -> `Pedido de matrícula (editable)`
   - `report_name`: `irg_pedido_matricula_rvoe.registration_order_rvoe_template` ->
     `irg_pedido_matricula_editable.registration_order_editable_template`
   - `report_file`: ídem, mismo cambio de módulo/template
   - El resto de campos del record se dejaron intactos (`model`, `report_type`,
     `print_report_name`, `binding_model_id` ref `sale.model_sale_order`,
     `binding_type`, `paperformat_id` ref
     `irg_sale_order_extended.report_registration_order_paperformat`).
2. El `<template id="...">`: `registration_order_rvoe_template` ->
   `registration_order_editable_template`. El cuerpo QWeb interno (todo el
   markup dentro de `web.html_container`/`web.basic_layout`) se dejó
   exactamente igual, sin tocar una sola línea, tal como exige la spec de
   "copia fiel".

No se modificó ningún otro archivo. No se tocó `irg_sale_order_extended` ni
`irg_pedido_matricula_rvoe`. No se realizaron commits git (branch `Dev_iRG`,
working tree con el nuevo módulo como untracked, igual que tras la Tarea 1).

Verificación adicional no exigida por el plan pero usada como chequeo de
sanidad: `wc -l` confirma que ambos archivos (RVOE y editable) tienen 805
líneas, y `grep -in "rvoe"` no encuentra ninguna coincidencia en el archivo
nuevo (case-insensitive), reforzando D4.

### Verificación de criterios de aceptación (ejecutados por el Coder)

- **D1** (XML sintácticamente válido):
  ```
  $ python3 -c "import xml.etree.ElementTree as ET; ET.parse('addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml'); print('OK')"
  OK
  ```
  Resultado: **PASA**

- **D2** (existen el record de acción y el template con los ids propios):
  ```
  $ python3 - <<'PY'
  ... (script del plan) ...
  PY
  OK
  ```
  Resultado: **PASA**

- **D3** (campos clave de la acción: name, model, report_name/report_file
  apuntando al template nuevo, binding_model_id, binding_type,
  paperformat_id):
  ```
  $ python3 - <<'PY'
  ... (script del plan) ...
  PY
  OK
  ```
  Resultado: **PASA**

- **D4** (sin branding RVOE, `grep -i "rvoe"` no encuentra coincidencias):
  ```
  $ ! grep -i "rvoe" "addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml" && echo OK
  OK
  ```
  Resultado: **PASA**

- **D5** (copia fiel del cuerpo del `<template>`, comparación por
  normalización de subárbol con id neutralizado):
  ```
  $ python3 - <<'PY'
  ... (script del plan) ...
  PY
  OK
  ```
  Resultado: **PASA**

### Estado de tareas del plan

- [x] Tarea 1 — Scaffold del módulo — IMPLEMENTADA, C1-C4 en verde (Coder).
- [x] Tarea 2 — Copia fiel del template QWeb + acción de reporte (XML único) —
  IMPLEMENTADA, criterios D1-D5 ejecutados y en verde por el Coder (pendiente
  de Review/Validate formal).
- [ ] Tarea 3 — Integridad del módulo completo (sin referencias rotas) —
  PENDIENTE (depende de Tareas 1 y 2, ya satisfechas; aún no ejecutada/verificada
  formalmente por el Coder en esta iteración).
- [ ] Tarea 4 (opcional) — Actualizar doc de conocimiento — PENDIENTE.

### Notas para la siguiente iteración

La Tarea 3 debe verificar de forma agregada: E1 (archivo de `data` existe en
disco — ya se cumple, pero falta ejecutarlo formalmente), E2 (los `ref`
externos del XML solo apuntan a `sale.*` o `irg_sale_order_extended.*`; en
este archivo los únicos refs son `sale.model_sale_order` y
`irg_sale_order_extended.report_registration_order_paperformat`, ambos
conformes) y E3 (no hay ids XML duplicados dentro del archivo del reporte).
E4 es condicional a runtime Docker y puede marcarse N/A si el entorno no
está disponible.

## Iteración 3 — Tarea 3: Integridad del módulo completo (sin referencias rotas)

**Fecha:** 2026-07-02
**Branch:** `Dev_iRG` (sin commits realizados)

### Qué se hizo

Se ejecutaron tal cual los tres criterios ejecutables (E1-E3) especificados en el
plan sobre el módulo ya creado en las Tareas 1 y 2
(`addons-extra/extrairg/irg_pedido_matricula_editable/`). No fue necesario
corregir nada: los tres pasaron a la primera ejecución, sin tocar ningún
archivo del módulo ni de `irg_sale_order_extended` / `irg_pedido_matricula_rvoe`.

Adicionalmente se comprobó disponibilidad de Docker (`docker ps`) para decidir
E4: el daemon Docker no está corriendo/disponible en este entorno
(`failed to connect to the docker API ... no such file or directory`), por lo
que E4 se marca **N/A** conforme a la nota del plan ("si Docker NO está
corriendo, se marca como N/A").

### Verificación de criterios de aceptación (ejecutados por el Coder)

- **E1** (todo archivo en `data` del manifiesto existe en disco):
  ```
  $ python3 - <<'PY'
  ... (script del plan) ...
  PY
  OK
  ```
  Resultado: **PASA**

- **E2** (los `ref` externos del XML apuntan solo a `sale.*` o
  `irg_sale_order_extended.*`, sin refs a `irg_pedido_matricula_rvoe`):
  ```
  $ python3 - <<'PY'
  ... (script del plan) ...
  PY
  OK
  ```
  Resultado: **PASA** (únicos refs presentes: `sale.model_sale_order` y
  `irg_sale_order_extended.report_registration_order_paperformat`)

- **E3** (no hay ids XML duplicados dentro del archivo del reporte):
  ```
  $ python3 - <<'PY'
  ... (script del plan) ...
  PY
  OK
  ```
  Resultado: **PASA**

- **E4** (verificación runtime, condicional a Docker):
  ```
  $ docker ps
  failed to connect to the docker API at unix:///Users/ivrogo/.docker/run/docker.sock;
  check if the path is correct and if the daemon is running: dial unix
  /Users/ivrogo/.docker/run/docker.sock: connect: no such file or directory
  ```
  Resultado: **N/A** — Docker no está disponible en este entorno de ejecución.
  No bloquea la tarea, conforme al criterio del plan.

### Estado de tareas del plan

- [x] Tarea 1 — Scaffold del módulo — IMPLEMENTADA, C1-C4 en verde (Coder).
- [x] Tarea 2 — Copia fiel del template QWeb + acción de reporte (XML único) —
  IMPLEMENTADA, D1-D5 en verde (Coder).
- [x] Tarea 3 — Integridad del módulo completo (sin referencias rotas) —
  IMPLEMENTADA/VERIFICADA por el Coder: E1, E2, E3 en verde; E4 marcada N/A
  (Docker no disponible). Pendiente de Review/Validate formal.
- [ ] Tarea 4 (opcional) — Actualizar doc de conocimiento — PENDIENTE (no se
  implementa en esta iteración; queda a decisión posterior según indicación
  del orquestador).

### Notas para la siguiente iteración

Con Tareas 1-3 implementadas y sus criterios ejecutados en verde por el Coder
(E4 N/A por falta de Docker), el módulo `irg_pedido_matricula_editable` está
completo según el alcance obligatorio del plan. La Tarea 4 (doc de
conocimiento) es opcional y no se ha tocado; se deja pendiente de decisión.
Ningún archivo de `irg_sale_order_extended` ni `irg_pedido_matricula_rvoe` fue
modificado en ningún momento. No se han realizado commits git.

## Iteración 4 — Tarea 4 (opcional): Actualizar la doc de conocimiento

**Fecha:** 2026-07-02
**Branch:** `Dev_iRG` (sin commits realizados)

### Qué se hizo

Se actualizó `.agents/knowledge/odoo_sale_order_custom_reports.md` añadiendo
una sección nueva ("Segundo ejemplo del patrón: reporte 'editable' con
dependencia mínima") al final del archivo, sin tocar el contenido previo
(que documenta el patrón RVOE). La sección nueva:

1. Registra el módulo `addons-extra/extrairg/irg_pedido_matricula_editable/`
   como segundo ejemplo del mismo patrón modular (módulo satélite que
   depende de `irg_sale_order_extended` y añade `ir.actions.report` +
   `<template>` propios sin tocar el módulo base).
2. Deja constancia explícita de la diferencia con el RVOE: el módulo RVOE
   declara `depends = ['irg_sale_order_extended', 'isep_openeducat_sale']`
   (usa `course_id`/`op.course` para el número/fecha de RVOE), mientras que
   `irg_pedido_matricula_editable` declara `depends = ['irg_sale_order_extended']`
   únicamente, por ser copia fiel del template original sin ese dato
   adicional.
3. Incluye el snippet XML del `ir.actions.report` nuevo
   (`action_report_registration_order_editable`) con sus campos clave
   (`report_name`/`report_file` apuntando a
   `irg_pedido_matricula_editable.registration_order_editable_template`,
   `paperformat_id` reutilizado de `irg_sale_order_extended`).
4. Añade una regla general (para futuros módulos satélite): declarar solo
   las dependencias que el template realmente usa, verificable comparando
   campos QWeb contra modelos de cada módulo candidato, en vez de copiar el
   `depends` de un módulo hermano por inercia.

No se modificó ningún archivo del módulo `irg_pedido_matricula_editable` ya
implementado (Tareas 1-3), ni `irg_sale_order_extended`, ni
`irg_pedido_matricula_rvoe`. Único archivo tocado en esta iteración:
`.agents/knowledge/odoo_sale_order_custom_reports.md`. No se realizaron
commits git.

### Verificación de criterios de aceptación (ejecutados por el Coder)

- **F1** (la doc menciona el nuevo módulo editable):
  ```
  $ grep -q "irg_pedido_matricula_editable" ".agents/knowledge/odoo_sale_order_custom_reports.md" && echo OK
  OK
  ```
  Resultado: **PASA**

- **F2** (la doc menciona el nuevo id de acción):
  ```
  $ grep -q "action_report_registration_order_editable" ".agents/knowledge/odoo_sale_order_custom_reports.md" && echo OK
  OK
  ```
  Resultado: **PASA**

### Estado de tareas del plan

- [x] Tarea 1 — Scaffold del módulo — IMPLEMENTADA, C1-C4 en verde (Coder).
- [x] Tarea 2 — Copia fiel del template QWeb + acción de reporte (XML único) —
  IMPLEMENTADA, D1-D5 en verde (Coder).
- [x] Tarea 3 — Integridad del módulo completo (sin referencias rotas) —
  IMPLEMENTADA/VERIFICADA por el Coder: E1, E2, E3 en verde; E4 marcada N/A
  (Docker no disponible).
- [x] Tarea 4 (opcional) — Actualizar doc de conocimiento — IMPLEMENTADA,
  F1-F2 en verde (Coder). Todas las tareas del plan (obligatorias 1-3 +
  opcional 4) quedan implementadas por el Coder, pendientes de Review/Validate
  formal.

### Notas para la siguiente iteración

Todas las tareas del plan (1-4) están implementadas y con sus criterios
ejecutados en verde por el Coder. No quedan tareas pendientes de
implementación. Corresponde ahora Review formal (`02b-review.md`) y
Validate formal (`03-validation.md`). Recordatorio: no se ha hecho ningún
commit git en toda la misión; el working tree en `Dev_iRG` contiene el
nuevo módulo `addons-extra/extrairg/irg_pedido_matricula_editable/`
(untracked) y la edición de
`.agents/knowledge/odoo_sale_order_custom_reports.md` (modified).

## Iteración 5 — Corrección: la Tarea 2 copió la fuente equivocada

**Fecha:** 2026-07-02
**Branch:** `Dev_iRG` (sin commits realizados)
**Realizado por:** orquestador (no por el subagente `coder`)

### Qué pasó

El Reviewer detectó (hallazgo marcado como MENOR, pero de fondo) que el plan
había asumido erróneamente que el módulo hermano `irg_pedido_matricula_rvoe`
(805 líneas) era "copia fiel del original de `irg_sale_order_extended`". Al
comparar contra el archivo real en disco
(`addons-extra/vztech/irg_sale_order_extended/reports/registration_order_template.xml`,
1532 líneas), el contenido difería sustancialmente (SEPA/domiciliación,
Orden de Pago con tarjeta, etc., ausentes en el RVOE).

Se verificó además contra la vista **viva** en la base de datos del servidor
beta (`ssh odoobetairg`, contenedor `nat16_pgodoo_latest`, DB `Base16`,
`SELECT arch_db->>'en_US' FROM ir_ui_view WHERE id=5285` — solo lectura, sin
tocar la BD) qué contenido es el que realmente se imprime hoy como "Pedido
de matrícula" en Odoo. La vista viva (1541 líneas) coincide en estructura y
contenido con el archivo en disco de `irg_sale_order_extended` (SEPA,
cláusulas 1-25, tri-firma, Orden de Pago con tarjeta) — el archivo en RVOE
(805 líneas) NO es una copia fiel del predeterminado real; es un contenido
distinto/recortado.

Confirmado también vía `ir_act_report_xml`: las acciones de impresión que
apuntan al `sale.order` para "Registration Order"/"Pedido de matrícula
Unimarconi" (id 1476) y "Pedido de matrícula RVOE" (id 1954) usan **el mismo**
`report_name` (`irg_sale_order_extended.registration_order_template`) — el
módulo git `irg_pedido_matricula_rvoe` aún no está instalado en beta; el
"RVOE" visible en el menú Imprimir hoy es una acción duplicada vía Studio del
mismo template original, no el nuevo módulo.

### Corrección aplicada

Se reemplazó el cuerpo del `<template id="registration_order_editable_template">`
en `addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml`
por el contenido real extraído de la vista viva (`ir_ui_view.id=5285`,
`Base16`), dejando intactos el record `ir.actions.report` y todos sus campos
(ya eran correctos). El archivo pasó de 805 a 1557 líneas.

Se re-ejecutaron todos los criterios automatizables:

- C1: OK · D1: OK · D3: OK · E1: OK · E2: OK · E3: OK
- Ids únicos tras el cambio: `action_report_registration_order_editable`,
  `registration_order_editable_template` (sin duplicados).
- `grep -ic "rvoe"` sobre el archivo: `0` (sin branding RVOE).

D2/D4 (ya cubiertos por los checks anteriores) y D5 quedan sin objeto en su
forma original (comparaba contra RVOE, que ya no es la fuente); la fidelidad
ahora se sustenta en que el contenido proviene directamente de la vista viva
en producción/beta, verificado por lectura SQL, no por diff contra otro
módulo del repo.

Se actualizó también `.agents/knowledge/odoo_sale_order_custom_reports.md`
con un nuevo gotcha documentando que el XML en git puede estar desactualizado
frente a `ir_ui_view.arch_db`, y cómo verificarlo (solo lectura).

### Estado de tareas del plan

- [x] Tarea 1 — Scaffold del módulo — sin cambios, sigue en verde.
- [x] Tarea 2 — CORREGIDA: ahora es copia fiel del predeterminado real
  (verificado contra la BD viva de beta), no del RVOE.
- [x] Tarea 3 — Integridad — re-verificada tras el cambio, en verde.
- [x] Tarea 4 — Doc actualizada con el gotcha adicional sobre arch_db vs git.

### Notas para Review/Validate

El Review anterior (si ya se había emitido `REVIEW OK` sobre el contenido
copiado del RVOE) queda OBSOLETO y debe repetirse sobre el archivo corregido.
