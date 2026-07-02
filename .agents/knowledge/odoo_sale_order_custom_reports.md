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
