# Spec: Duplicado editable del informe "Pedido de matrícula" (sale.order)

## Objetivo
Crear un nuevo módulo Odoo 16, `irg_pedido_matricula_editable`, que duplique de forma
idéntica el informe predeterminado de "Pedido de matrícula" del `sale.order`
(`irg_sale_order_extended.registration_order_template`) en una plantilla QWeb propia,
accesible desde el botón "Imprimir" del formulario de Pedido de Ventas, para poder
editar layout/contenido de forma libre sin tocar el original ni el módulo RVOE ya
existente.

## Contexto de referencia
Ya existe un módulo gemelo con el mismo patrón: `irg_pedido_matricula_rvoe`
(`addons-extra/extrairg/irg_pedido_matricula_rvoe/`, commit 30d2b4bd). Ese módulo:
- Duplica `irg_sale_order_extended.registration_order_template` en
  `reports/registration_order_rvoe_template.xml` con id propio
  (`registration_order_rvoe_template`).
- Declara un `ir.actions.report` con `binding_model_id="sale.model_sale_order"`,
  `binding_type="report"` y `report_name`/`report_file` apuntando al nuevo template,
  reutilizando `paperformat_id="irg_sale_order_extended.report_registration_order_paperformat"`.
- Manifiesto declara dependencia de `irg_sale_order_extended`.
- Documentado en `.agents/knowledge/odoo_sale_order_custom_reports.md`.

Este módulo nuevo debe seguir el mismo patrón, pero:
- Nombre de módulo: `irg_pedido_matricula_editable`.
- Nombre visible del reporte/acción: "Pedido de matrícula (editable)" (no usar
  branding RVOE, es una copia genérica de IRG para edición libre).
- Debe ser completamente independiente: no depende de `irg_pedido_matricula_rvoe`,
  solo de `irg_sale_order_extended` (dependencia mínima para heredar el paperformat
  y el modelo `course_id` en `sale.order`).

## Alcance
1. Scaffold del módulo `addons-extra/extrairg/irg_pedido_matricula_editable/`:
   `__init__.py`, `__manifest__.py`.
2. Duplicar la plantilla QWeb original completa
   (`irg_sale_order_extended.registration_order_template`) en
   `reports/registration_order_editable_template.xml` con id propio
   `registration_order_editable_template`, contenido idéntico al original en el
   momento de la copia.
3. Definir `ir.actions.report` (`action_report_registration_order_editable`)
   vinculando el nuevo template a `sale.order` vía `binding_model_id`, para que
   aparezca en el menú "Imprimir" como "Pedido de matrícula (editable)".
4. Registrar el XML del reporte en `data` del manifiesto.

## Fuera de alcance
- No modificar `irg_sale_order_extended` ni `irg_pedido_matricula_rvoe`.
- No tocar lógica de `sale.order` (Python), es solo duplicado de vista/reporte QWeb.

## Criterios de aceptación
- El módulo instala sin errores (o al menos: XML válido sintácticamente, manifiesto
  correcto, sin referencias rotas).
- El template QWeb nuevo es una copia fiel del original (mismo contenido, ids propios).
- El botón "Imprimir" de `sale.order` muestra la nueva opción
  "Pedido de matrícula (editable)".
- Documentación de conocimiento (`.agents/knowledge/odoo_sale_order_custom_reports.md`)
  actualizada si aplica (nuevo binding registrado).
