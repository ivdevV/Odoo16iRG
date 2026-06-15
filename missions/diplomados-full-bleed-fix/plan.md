# Mission: diplomados-full-bleed-fix

## Objetivo
Resolver la presencia de márgenes/bordes blancos residuales (no full bleed) en los diplomas PDF generados por `irg_generacion_diplomados` al ajustar la estructura de anidación del layout.

## Diagnóstico
Se detectó un doble anidamiento de etiquetas `<html>` y `<body>`. Esto ocurre porque la plantilla principal `report_diplomado_template` llama a `web.html_container`, y dentro del bucle llama a `web.basic_layout`, la cual vuelve a invocar a `web.html_container` en Odoo 16. Este doble anidamiento impide que el motor wkhtmltopdf procese la directiva `@page { margin: 0 !important; }` correctamente, generando márgenes predeterminados no deseados.

## Clasificación de complejidad
`trivial`: Ajuste de la estructura del template QWeb (`diplomado_templates.xml`) removiendo la etiqueta externa redundante `web.html_container`.

## Implementación
- Eliminar la etiqueta externa `<t t-call="web.html_container">` en `diplomado_templates.xml`.
- Mantener el bucle `<t t-foreach="docs" t-as="o">` a nivel de raíz y dejar que llame a `web.basic_layout` directamente. Esto elimina el doble anidamiento de `html_container` asegurando que wkhtmltopdf renderice a hoja completa.

## Validación
- Ejecución de las pruebas unitarias del módulo: `docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_generacion_diplomados --test-enable --test-tags=irg_generacion_diplomados --stop-after-init`
- Regeneración local del PDF y HTML mediante script: `docker exec -i odoo16irg_local odoo shell -c /etc/odoo/odoo.conf -d test_irg_db --stop-after-init < scratch/generate_pdf.py`
- Inspección manual del HTML generado (`test_output.html`) para comprobar la estructura de etiquetas limpia y del PDF (`test_output.pdf`) para corroborar la desaparición de bordes blancos.
