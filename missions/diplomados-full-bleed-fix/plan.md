# Mission: diplomados-full-bleed-fix

## Objetivo
Conseguir que el fondo (diploma_background.jpg) y el contenido del diploma ocupen
exactamente toda la hoja A4 Landscape (297×210mm) sin bordes blancos en ningún borde.

## Diagnóstico
El paperformat ya tiene márgenes a 0. El problema es que `web.basic_layout` inyecta
un wrapper `.page` con `padding-top: Xmm` (el valor del header_spacing del paperformat)
y estilos propios que reducen el área de renderizado. wkhtmltopdf aplica el margen de
página sobre ese viewport reducido, dejando bandas blancas.

## Solución
Usar `web.html_container` directamente sin `web.basic_layout`. El HTML resultante será
más limpio y wkhtmltopdf renderizará el contenido contra el viewport completo de la página.
El `<div class="page">` de Odoo también añade padding; se elimina con `!important` o se
reemplaza por un div propio sin esa clase.

Adicionalmente, usar `position: fixed; inset: 0` en la imagen de fondo (en lugar de
`position: absolute`) para que wkhtmltopdf la ancle al viewport de la página física y
no al contenedor relativo, garantizando full bleed real.

## Archivos afectados
- `addons-extra/extrairg/irg_generacion_diplomados/reports/diplomado_templates.xml`

## Clasificación de complejidad
`standard`: 1 archivo, lógica QWeb acotada.

## Criterios de éxito
- xmllint sin errores.
- Odoo carga sin errores.
- PDF generado: fondo ocupa toda la hoja A4 Landscape sin bordes blancos.

## Modelo usado
standard (claude-sonnet)
