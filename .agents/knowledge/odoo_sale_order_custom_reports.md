# Odoo Custom Reports binding in sale.order (IRG)

## Contexto y Decisiones
Al crear reportes adicionales de impresión (PDF QWeb) vinculados al modelo `sale.order` (por ejemplo, reportes alternativos como la matrícula RVOE), se debe utilizar el sistema modular de Odoo para evitar modificar componentes base de terceros.

* **Estrategia modular**: En lugar de modificar directamente `irg_sale_order_extended`, se recomienda crear un módulo de extensión independiente que declare la dependencia de `irg_sale_order_extended` en su manifiesto.
* **Modelo Asociado**: `sale.order` ya cuenta con el campo `course_id` (de `op.course`), lo cual permite recuperar de forma directa los metadatos de RVOE (número y fecha) sin necesidad de redefinir o buscar mediante queries complejos.

## Convenciones y Snippets de Reporte
Para registrar la acción y vincularla al botón "Imprimir" en Odoo 16:
```xml
<record id="action_report_registration_order_rvoe" model="ir.actions.report">
    <field name="name">Pedido de matrícula RVOE</field>
    <field name="model">sale.order</field>
    <field name="report_type">qweb-pdf</field>
    <field name="report_name">irg_pedido_matricula_rvoe.registration_order_rvoe_template</field>
    <field name="report_file">irg_pedido_matricula_rvoe.registration_order_rvoe_template</field>
    <field name="print_report_name">object.name</field>
    <field name="binding_model_id" ref="sale.model_sale_order"/>
    <field name="binding_type">report</field>
    <field name="paperformat_id" ref="irg_sale_order_extended.report_registration_order_paperformat"/>
</record>
```

## Gotchas y Notas de Implementación
* Usar `ref="sale.model_sale_order"` para la vinculación en el botón "Imprimir".
* Si el demonio de Docker del entorno local no está corriendo en el host del desarrollador, se debe recurrir al testeo sintáctico XML (`xml.etree.ElementTree`) para verificar la compilación previa antes de subir los cambios.
* **El archivo `.xml` en git puede estar desactualizado frente a la vista viva en la BD.** Odoo guarda el arch de cada `<template>`/`<report>` en `ir_ui_view.arch_db` (jsonb); si alguien lo editó vía Studio/backend sin volcar el cambio al repo, el archivo en disco diverge del PDF real que ve el usuario. Antes de asumir que un archivo del repo es "el predeterminado", comparar contra la vista viva: `docker exec <pg_container> psql -U odoo -d <db> -t -A -c "SELECT arch_db->>'en_US' FROM ir_ui_view WHERE key='<module>.<template_id>';"` (solo lectura). Caso real (2026-07-02): `irg_sale_order_extended/reports/registration_order_template.xml` en git tenía pequeñas diferencias de texto frente a `ir_ui_view.id=5285` en `Base16` (servidor beta) — se usó el contenido de la BD como fuente de verdad para duplicar el reporte en `irg_pedido_matricula_editable`.

## Segundo ejemplo del patrón: reporte "editable" con dependencia mínima

El mismo patrón modular (módulo satélite que declara `depends` sobre
`irg_sale_order_extended` y añade un `ir.actions.report` + `<template>`
propios, sin tocar el módulo base) se replicó en
`addons-extra/extrairg/irg_pedido_matricula_editable/` para el reporte
"Pedido de matrícula (editable)".

* **Diferencia clave frente al RVOE**: el módulo RVOE
  (`addons-extra/extrairg/irg_pedido_matricula_rvoe/`) declara en su
  manifiesto `depends = ['irg_sale_order_extended', 'isep_openeducat_sale']`
  porque su template usa metadatos de `course_id` (`op.course`, vía
  `isep_openeducat_sale`) para mostrar número y fecha de RVOE. El módulo
  `irg_pedido_matricula_editable`, en cambio, es una copia fiel del cuerpo
  QWeb original de `irg_sale_order_extended` **sin** ese branding/dato
  adicional, por lo que su manifiesto declara
  `depends = ['irg_sale_order_extended']` — dependencia mínima única,
  verificada explícitamente para no arrastrar `isep_openeducat_sale` ni
  `irg_pedido_matricula_rvoe`.
* **Archivo único** `reports/registration_order_editable_template.xml`
  contiene, igual que en el RVOE, tanto el record `ir.actions.report` como
  el `<template>` en el mismo XML (`<odoo><data>...</data></odoo>`):
  ```xml
  <record id="action_report_registration_order_editable" model="ir.actions.report">
      <field name="name">Pedido de matrícula (editable)</field>
      <field name="model">sale.order</field>
      <field name="report_type">qweb-pdf</field>
      <field name="report_name">irg_pedido_matricula_editable.registration_order_editable_template</field>
      <field name="report_file">irg_pedido_matricula_editable.registration_order_editable_template</field>
      <field name="print_report_name">object.name</field>
      <field name="binding_model_id" ref="sale.model_sale_order"/>
      <field name="binding_type">report</field>
      <field name="paperformat_id" ref="irg_sale_order_extended.report_registration_order_paperformat"/>
  </record>
  ```
* El `<template id="registration_order_editable_template">` reutiliza el
  `paperformat_id` ya definido en `irg_sale_order_extended`
  (`irg_sale_order_extended.report_registration_order_paperformat`), igual
  que el RVOE, evitando duplicar la definición de paperformat.
* Regla general reforzada por este segundo ejemplo: cada módulo satélite de
  reporte debe declarar SOLO las dependencias que su template realmente
  necesita (verificable comparando los campos usados en el QWeb contra los
  modelos de cada módulo candidato), en vez de copiar por inercia el
  `depends` de un módulo hermano ya existente.
