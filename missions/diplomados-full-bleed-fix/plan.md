# Mission: diplomados-full-bleed-fix

## Objetivo
Resolver la presencia de márgenes/bordes blancos residuales (no full bleed) en los diplomas PDF generados por `irg_generacion_diplomados` al ajustar la estructura de anidación del layout.

## Diagnóstico
- Se detectó un doble anidamiento de etiquetas `<html>` y `<body>` por el uso de `web.html_container` en combinación con `web.basic_layout`. Esto impedía el procesamiento de `@page { margin: 0; }`.
- Adicionalmente, se descubrió que Odoo aplica la clase Bootstrap `.container` al `<body>`, la cual tiene un ancho fijo (por ejemplo, `970px` o `1170px`) según la resolución simulada por `wkhtmltopdf`. Esto encogía la página de renderizado y generaba márgenes blancos en los cuatro costados.

## Clasificación de complejidad
`trivial`: Ajuste en el template QWeb (`diplomado_templates.xml`) para eliminar la estructura anidada y sobreescribir las restricciones de ancho de Bootstrap.

## Implementación
- Eliminar la etiqueta externa `<t t-call="web.html_container">` en `diplomado_templates.xml`.
- Mantener el bucle `<t t-foreach="docs" t-as="o">` llamando a `web.basic_layout` directamente.
- Añadir `width: 100% !important; max-width: none !important; min-width: 0 !important;` en el bloque de estilos del documento para forzar a que el body y sus elementos contenedores ocupen todo el ancho físico.

## Validación
- Ejecución de las pruebas unitarias del módulo: `docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_generacion_diplomados --test-enable --test-tags=irg_generacion_diplomados --stop-after-init`
- Regeneración local del PDF y HTML mediante script: `docker exec -i odoo16irg_local odoo shell -c /etc/odoo/odoo.conf -d test_irg_db --stop-after-init < scratch/generate_pdf.py`
- Inspección manual del HTML generado (`test_output.html`) y confirmación de que la página se extiende al 100% de la pantalla/viewport sin restricciones de ancho.
