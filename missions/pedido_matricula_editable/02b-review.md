# Review — Misión `pedido_matricula_editable`

## Iteración 1 (OBSOLETA — sobre contenido incorrecto, ver Iteración 2 más abajo)

Revisión emitida por el subagente `reviewer` sobre el estado tras la
Iteración 4 de `02-progress.md`, cuando el `<template>` todavía era copia del
módulo RVOE (805 líneas) en vez del predeterminado real. El propio hallazgo
de esta revisión (MENOR) fue el disparador de la corrección aplicada en la
Iteración 5 de `02-progress.md`. Se conserva aquí solo como registro.

**Reviewer:** juicio por lectura (sin ejecución) — **Branch:** Dev_iRG

### Hallazgo MENOR (el que motivó la corrección)
- Archivo: `.agents/knowledge/odoo_sale_order_custom_reports.md` y premisa del
  plan (`01-plan.md`, "Nota sobre copia fiel").
- El template entregado en ese momento NO era copia del archivo en disco
  `addons-extra/vztech/irg_sale_order_extended/reports/registration_order_template.xml`
  (1533 líneas, contenido SEPA/Orden de Pago) sino copia byte-idéntica del
  hermano RVOE (805 líneas, cláusulas 1-24, tri-firma).
- El reviewer no lo bloqueó porque el plan designaba explícitamente al RVOE
  como fuente — pero verificación posterior contra la BD viva del servidor
  beta confirmó que el archivo en disco de `irg_sale_order_extended` (no el
  RVOE) es el que coincide con el predeterminado real.

Resto de verificaciones (manifiesto, XML válido, sin refs rotas, sin ids
duplicados, sin branding RVOE, módulos base intactos): todas OK en esa
iteración y siguen OK tras la corrección (no dependían del cuerpo del
template).

---

## Iteración 2 (VIGENTE — sobre el contenido corregido)

**Reviewer:** juicio por lectura (sin ejecución) — **Branch:** Dev_iRG
**Fecha:** 2026-07-02
**Estado revisado:** template reemplazado por el contenido real extraído de
`ir_ui_view.id=5285` en `Base16` (ver Iteración 5 de `02-progress.md`). Archivo
`registration_order_editable_template.xml` = 1557 líneas.

### Arquitectura y plan
- Tarea 1 (manifiesto) OK: `depends = ['irg_sale_order_extended']` EXACTO (sin
  `isep_openeducat_sale` ni `irg_pedido_matricula_rvoe`); `data` lista
  `reports/registration_order_editable_template.xml`; `version` 16.0.1.0.0,
  `license` LGPL-3, `installable` True, `auto_install` False. Encaja con el
  patrón modular satélite descrito en el plan.
- `__init__.py` correcto (solo cabecera de codificación).
- Archivo XML único con `ir.actions.report` + `<template>`, misma organización
  que el RVOE, tal como pide el plan.

### Calidad / integridad del XML
- IDs propios correctos y únicos: `action_report_registration_order_editable`
  y `registration_order_editable_template`. No hay ids duplicados.
- Record de acción con todos los campos clave correctos: `name` = "Pedido de
  matrícula (editable)", `model` = sale.order, `report_type` = qweb-pdf,
  `report_name`/`report_file` apuntando al template propio del módulo,
  `print_report_name` = object.name, `binding_model_id` ref
  `sale.model_sale_order`, `binding_type` = report, `paperformat_id` ref
  `irg_sale_order_extended.report_registration_order_paperformat`.
- Refs externos: SOLO `sale.model_sale_order` e
  `irg_sale_order_extended.report_registration_order_paperformat`; ambos dentro
  de la única dependencia declarada. Sin refs rotas ni a RVOE.
- Sin branding RVOE: `grep -i rvoe` = 0 coincidencias.
- Estructura QWeb bien formada y balanceada:
  `web.html_container` (t-no-header/t-no-footer) > `t-foreach docs` >
  `web.basic_layout` > 3 bloques `<div class="page">` (líneas 20-614, 616-811,
  813-1550, este último con page-break y contenido SEPA/domiciliación + Orden
  de Pago con tarjeta/Stripe). Cierre limpio `</template></data></odoo>`. No hay
  tags huérfanos ni truncamientos a mitad de frase.
- Coherencia con la fuente: la estructura coincide con el original de git
  `addons-extra/vztech/irg_sale_order_extended/reports/registration_order_template.xml`
  (misma cabecera, mismas 3 páginas, mismo cierre), omitiendo solo el `<t
  t-name>` interno redundante — divergencia explícitamente permitida por el
  plan. Incluye el contenido SEPA/Orden de Pago ausente en el RVOE (805 líneas),
  confirmando que ya NO es copia de la fuente equivocada.

### Seguridad / zonas sensibles
- No se toca lógica Python de `sale.order`. Solo QWeb/reporte.
- `irg_sale_order_extended` NO modificado; `irg_pedido_matricula_rvoe` intacto
  (sigue apuntando a su propio template `registration_order_rvoe_template`).
- Módulo nuevo untracked; sin credenciales ni secretos; sin inputs de usuario;
  la extracción desde `ir_ui_view.arch_db` fue de solo lectura (documentada como
  gotcha en la doc de conocimiento).

### Hallazgos
- Sin hallazgos BLOQUEANTES.
- NIT: el `report_name` con módulo `irg_pedido_matricula_editable` es válido pero
  depende de que el nombre técnico del módulo coincida exactamente en instalación
  (no bloquea; es el estándar Odoo). No requiere acción.

REVIEW OK
