# Plan: Duplicado editable del informe "Pedido de matrícula" (sale.order)

## Contexto de referencia (verificado en el repo)

- Branch de trabajo: `Dev_iRG`. NO usar `main` como base.
- No existe `PROJECT.md`. No hay comandos de test/build/lint declarados a nivel de
  proyecto. Por ello, los criterios de aceptación se basan en verificaciones
  ejecutables locales y deterministas (validación XML, presencia de records,
  ausencia de referencias rotas por comparación textual), no en una suite de tests
  del proyecto.
- Módulo base (origen de la copia):
  `addons-extra/vztech/irg_sale_order_extended/`
  - Template original: `reports/registration_order_template.xml`,
    template id externo `irg_sale_order_extended.registration_order_template`.
  - Paperformat reutilizable: `reports/registration_order_paperformat.xml`,
    id externo `irg_sale_order_extended.report_registration_order_paperformat`.
  - Todos los campos que usa el template (`student_id`, `initial_payment`,
    `rest_postponed`, `payment_mode_id`, `is_official`, `formation_type`, etc.)
    están definidos DENTRO de `irg_sale_order_extended`
    (`models/sale_order.py`, `models/product_template.py`). Esto confirma que la
    dependencia mínima única `irg_sale_order_extended` es suficiente y correcta.
- Módulo hermano ya implementado (patrón exacto a replicar):
  `addons-extra/extrairg/irg_pedido_matricula_rvoe/`
  - `__init__.py` (solo cabecera `# -*- coding: utf-8 -*-`),
    `__manifest__.py`, `reports/registration_order_rvoe_template.xml`.
  - Ojo: el manifiesto del hermano RVOE declara además `isep_openeducat_sale`
    como dependencia. Para ESTE módulo la spec exige dependencia mínima: solo
    `irg_sale_order_extended` (ver Tarea 2, criterio D2).
- Nuevo módulo a crear: `addons-extra/extrairg/irg_pedido_matricula_editable/`.
- IDs propios exigidos por la spec:
  - Template: `registration_order_editable_template`.
  - Acción de reporte: `action_report_registration_order_editable`.
  - Nombre visible del reporte/acción: `Pedido de matrícula (editable)`.

## Diferencia clave respecto al patrón RVOE

En el módulo RVOE la acción `ir.actions.report` y el `<template>` conviven en el
MISMO archivo XML. Se mantiene esa misma organización aquí: un único archivo
`reports/registration_order_editable_template.xml` que contiene tanto el record
`ir.actions.report` como el `<template>`. La única diferencia funcional frente al
RVOE es el naming (editable en vez de RVOE) y que NO se añade branding RVOE ni
contenido nuevo: el cuerpo del template debe ser copia fiel del original de
`irg_sale_order_extended`.

## Nota sobre "copia fiel" del template

El template original define el id como
`<template id="irg_sale_order_extended.registration_order_template">` con un
`<t t-name="...">` interno redundante. En el módulo hermano RVOE la copia se
simplificó a `<template id="registration_order_rvoe_template">` (sin el
`t-name` interno) y ese template renderiza correctamente. Por tanto "copia fiel"
significa: cuerpo QWeb idéntico (mismo markup dentro de
`web.html_container` / `web.basic_layout`), con el id externo propio del módulo
nuevo. Se toma como fuente de copia el cuerpo del template ya normalizado en
`irg_pedido_matricula_rvoe/reports/registration_order_rvoe_template.xml`
(idéntico al original salvo id), garantizando fidelidad verificable por diff.

---

## Tareas atómicas

### Tarea 1 — Scaffold del módulo (`__init__.py` + `__manifest__.py`)

Crear el directorio `addons-extra/extrairg/irg_pedido_matricula_editable/` con:

- `__init__.py` con únicamente la cabecera de codificación:
  ```python
  # -*- coding: utf-8 -*-
  ```
- `__manifest__.py` con:
  - `name`: `IRG Pedido de Matrícula (editable)`
  - `version`: `16.0.1.0.0`
  - `summary`: descripción del reporte editable de Pedido de Matrícula para sale.order
  - `category`: `Sale`
  - `depends`: EXACTAMENTE `['irg_sale_order_extended']` (dependencia mínima única)
  - `data`: `['reports/registration_order_editable_template.xml']`
  - `installable`: `True`, `auto_install`: `False`, `license`: `LGPL-3`

**Dependencias:** ninguna (primera tarea).

**Criterios de aceptación (ejecutables desde la raíz del repo):**

- C1 — Existen ambos archivos:
  ```bash
  test -f "addons-extra/extrairg/irg_pedido_matricula_editable/__init__.py" \
    && test -f "addons-extra/extrairg/irg_pedido_matricula_editable/__manifest__.py" \
    && echo OK
  ```
  Pasa si imprime `OK`.

- C2 — El manifiesto es un dict Python válido y evaluable:
  ```bash
  python3 -c "import ast; ast.literal_eval(open('addons-extra/extrairg/irg_pedido_matricula_editable/__manifest__.py').read()); print('OK')"
  ```
  Pasa si imprime `OK` sin excepción.

- C3 — `depends` es exactamente `['irg_sale_order_extended']` (no incluye
  `isep_openeducat_sale` ni `irg_pedido_matricula_rvoe`):
  ```bash
  python3 -c "import ast; d=ast.literal_eval(open('addons-extra/extrairg/irg_pedido_matricula_editable/__manifest__.py').read()); assert d['depends']==['irg_sale_order_extended'], d['depends']; print('OK')"
  ```
  Pasa si imprime `OK`.

- C4 — `data` referencia el XML del reporte:
  ```bash
  python3 -c "import ast; d=ast.literal_eval(open('addons-extra/extrairg/irg_pedido_matricula_editable/__manifest__.py').read()); assert 'reports/registration_order_editable_template.xml' in d['data']; print('OK')"
  ```
  Pasa si imprime `OK`.

---

### Tarea 2 — Copia fiel del template QWeb + acción de reporte (XML único)

Crear `addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml`
con la misma estructura de un solo archivo `<odoo><data>...</data></odoo>` que el
módulo RVOE, conteniendo:

1. Un record `ir.actions.report` con:
   - `id`: `action_report_registration_order_editable`
   - `name`: `Pedido de matrícula (editable)`
   - `model`: `sale.order`
   - `report_type`: `qweb-pdf`
   - `report_name`: `irg_pedido_matricula_editable.registration_order_editable_template`
   - `report_file`: `irg_pedido_matricula_editable.registration_order_editable_template`
   - `print_report_name`: `object.name`
   - `binding_model_id` ref `sale.model_sale_order`
   - `binding_type`: `report`
   - `paperformat_id` ref `irg_sale_order_extended.report_registration_order_paperformat`
2. Un `<template id="registration_order_editable_template">` cuyo cuerpo QWeb sea
   copia fiel del cuerpo de
   `addons-extra/extrairg/irg_pedido_matricula_rvoe/reports/registration_order_rvoe_template.xml`
   (que a su vez es copia fiel del original de `irg_sale_order_extended`),
   sin cambios de contenido salvo el `id` del template.

**Dependencias:** Tarea 1 (el manifiesto ya debe referenciar este archivo).

**Criterios de aceptación (ejecutables desde la raíz del repo):**

- D1 — El XML es sintácticamente válido:
  ```bash
  python3 -c "import xml.etree.ElementTree as ET; ET.parse('addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml'); print('OK')"
  ```
  Pasa si imprime `OK` sin excepción.

- D2 — Existen exactamente el record de acción y el template con los ids propios:
  ```bash
  python3 - <<'PY'
  import xml.etree.ElementTree as ET
  r = ET.parse('addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml').getroot()
  ids = [e.get('id') for e in r.iter() if e.get('id')]
  assert 'action_report_registration_order_editable' in ids, ids
  assert 'registration_order_editable_template' in ids, ids
  print('OK')
  PY
  ```
  Pasa si imprime `OK`.

- D3 — La acción tiene los campos clave correctos (name, binding, paperformat,
  report_name/report_file apuntando al template nuevo):
  ```bash
  python3 - <<'PY'
  import xml.etree.ElementTree as ET
  r = ET.parse('addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml').getroot()
  rec = [e for e in r.iter('record') if e.get('id')=='action_report_registration_order_editable'][0]
  f = {fld.get('name'): (fld.text.strip() if fld.text else fld.get('ref')) for fld in rec.findall('field')}
  assert f['name']=='Pedido de matrícula (editable)', f['name']
  assert f['model']=='sale.order'
  assert f['report_name']=='irg_pedido_matricula_editable.registration_order_editable_template', f['report_name']
  assert f['report_file']=='irg_pedido_matricula_editable.registration_order_editable_template'
  assert f['binding_model_id']=='sale.model_sale_order'
  assert f['binding_type']=='report'
  assert f['paperformat_id']=='irg_sale_order_extended.report_registration_order_paperformat'
  print('OK')
  PY
  ```
  Pasa si imprime `OK`.

- D4 — Sin branding RVOE en el nuevo archivo (no debe contener la cadena `rvoe`
  ni `RVOE` en ids/refs, para garantizar independencia del módulo RVOE):
  ```bash
  ! grep -i "rvoe" "addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml" && echo OK
  ```
  Pasa si imprime `OK` (grep no encuentra coincidencias).

- D5 — Copia fiel del cuerpo del template: el markup del `<template>` nuevo es
  idéntico al del RVOE salvo el atributo `id` del `<template>`. Verificación por
  extracción y normalización del subárbol `<template>`:
  ```bash
  python3 - <<'PY'
  import xml.etree.ElementTree as ET
  def body(path):
      r = ET.parse(path).getroot()
      t = [e for e in r.iter('template')][0]
      t.set('id','X')  # neutraliza el id para comparar solo el cuerpo
      return ET.tostring(t, encoding='unicode')
  new = body('addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml')
  ref = body('addons-extra/extrairg/irg_pedido_matricula_rvoe/reports/registration_order_rvoe_template.xml')
  assert new == ref, 'El cuerpo del template NO es copia fiel del original'
  print('OK')
  PY
  ```
  Pasa si imprime `OK`. (Si el implementador copia directamente el cuerpo del
  RVOE cambiando solo el `id`, este criterio pasa de forma trivial y garantiza
  fidelidad al original de `irg_sale_order_extended`.)

---

### Tarea 3 — Integridad del módulo completo (sin referencias rotas)

Verificación agregada de que el módulo es coherente como conjunto: el archivo
listado en `data` existe, los `ref` externos usados apuntan a módulos declarados
en `depends` o a módulos base de Odoo conocidos (`sale`), y no hay ids duplicados.

**Dependencias:** Tareas 1 y 2.

**Criterios de aceptación (ejecutables desde la raíz del repo):**

- E1 — Todo archivo en `data` del manifiesto existe en disco:
  ```bash
  python3 - <<'PY'
  import ast, os
  base='addons-extra/extrairg/irg_pedido_matricula_editable'
  d=ast.literal_eval(open(os.path.join(base,'__manifest__.py')).read())
  for f in d['data']:
      assert os.path.isfile(os.path.join(base,f)), f
  print('OK')
  PY
  ```
  Pasa si imprime `OK`.

- E2 — Los `ref` externos del XML apuntan a `sale.*` o a `irg_sale_order_extended.*`
  (única dependencia); no hay refs a `irg_pedido_matricula_rvoe`:
  ```bash
  python3 - <<'PY'
  import xml.etree.ElementTree as ET
  r = ET.parse('addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml').getroot()
  refs = [fld.get('ref') for fld in r.iter('field') if fld.get('ref')]
  for ref in refs:
      mod = ref.split('.')[0]
      assert mod in ('sale','irg_sale_order_extended'), ref
  print('OK')
  PY
  ```
  Pasa si imprime `OK`.

- E3 — No hay ids XML duplicados dentro del archivo del reporte:
  ```bash
  python3 - <<'PY'
  import xml.etree.ElementTree as ET
  r = ET.parse('addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml').getroot()
  ids=[e.get('id') for e in r.iter() if e.get('id')]
  assert len(ids)==len(set(ids)), ids
  print('OK')
  PY
  ```
  Pasa si imprime `OK`.

- E4 (verificación runtime, condicional al entorno Docker) — Si el entorno local
  de Odoo está disponible, instalar/actualizar el módulo y comprobar que carga
  sin error y que la acción queda registrada. Este criterio es el único que
  requiere runtime; si Docker NO está corriendo, se marca como N/A y bastan
  E1–E3 + D1–D5 (validación sintáctica y estructural) según la nota de PROJECT
  ausente. Comando de referencia (ajustar contenedor/DB del entorno beta,
  `container nat16_pgodoo_latest`, DB `Base16` — NO tocar su DB directamente en
  producción; usar DB de pruebas):
  ```bash
  # Ejemplo (entorno de pruebas):
  # docker exec <contenedor> odoo -d <db_pruebas> -u irg_pedido_matricula_editable --stop-after-init
  # -> log sin "ERROR"/"CRITICAL" y sin "ParseError" referidos al módulo
  ```
  Pasa si el log de actualización no contiene errores del módulo y la acción
  `action_report_registration_order_editable` aparece registrada. Marcar N/A si
  el runtime no está disponible.

---

### Tarea 4 (opcional) — Actualizar la doc de conocimiento

Actualizar `.agents/knowledge/odoo_sale_order_custom_reports.md` para registrar el
nuevo binding editable como segundo ejemplo del mismo patrón (junto al RVOE),
dejando constancia de que el módulo editable depende SOLO de
`irg_sale_order_extended`.

**Dependencias:** Tareas 1–3 (documenta lo ya implementado).

**Criterios de aceptación (ejecutables desde la raíz del repo):**

- F1 — La doc menciona el nuevo módulo editable:
  ```bash
  grep -q "irg_pedido_matricula_editable" ".agents/knowledge/odoo_sale_order_custom_reports.md" && echo OK
  ```
  Pasa si imprime `OK`.

- F2 — La doc menciona el nuevo id de acción:
  ```bash
  grep -q "action_report_registration_order_editable" ".agents/knowledge/odoo_sale_order_custom_reports.md" && echo OK
  ```
  Pasa si imprime `OK`.

(Esta tarea es OPCIONAL según la spec: "actualizada si aplica". Puede omitirse sin
bloquear el `PASS global`, pero si se ejecuta debe cumplir F1 y F2.)

---

## Orden de ejecución y dependencias

1. **Tarea 1** (scaffold) — sin dependencias.
2. **Tarea 2** (template + acción) — depende de Tarea 1.
3. **Tarea 3** (integridad) — depende de Tareas 1 y 2.
4. **Tarea 4** (doc, opcional) — depende de Tareas 1–3.

## Alcance / Fuera de alcance (recordatorio de la spec)

- NO modificar `irg_sale_order_extended` ni `irg_pedido_matricula_rvoe`.
- NO tocar lógica Python de `sale.order`. Solo scaffold + XML de reporte (+ doc).
- Trabajo sobre branch `Dev_iRG`.

## Resumen de archivos a crear

- `addons-extra/extrairg/irg_pedido_matricula_editable/__init__.py`
- `addons-extra/extrairg/irg_pedido_matricula_editable/__manifest__.py`
- `addons-extra/extrairg/irg_pedido_matricula_editable/reports/registration_order_editable_template.xml`
- (opcional) edición de `.agents/knowledge/odoo_sale_order_custom_reports.md`
