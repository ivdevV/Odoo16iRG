# Mission: diplomados-scale-wrapper

## Objetivo
Hacer que el diploma ocupe visualmente mas superficie de la hoja A4 Landscape sin eliminar `web.basic_layout`, ya que quitarlo rompio el render del reporte.

## Diagnostico
El paperformat ya es A4 Landscape con margenes 0. El problema visible es que wkhtmltopdf/Odoo renderiza el contenido dentro de una caja interna ligeramente menor que la hoja real. Para evitar tocar de nuevo la estructura base del reporte, se escala el contenido interno de cada pagina manteniendo el layout estable.

## Clasificacion de complejidad
`standard`: cambio acotado en un template QWeb, con impacto visual en anverso y reverso.

## Implementacion
- Mantener `web.basic_layout`.
- Mantener los contenedores `.page diploma-page`.
- Anadir un wrapper `.diploma-scale` dentro de cada pagina.
- Mover fondo, textos, logo y firmas dentro del wrapper.
- Aplicar `transform: scale(1.08)` con `transform-origin: center center`.
- Usar `left: 50%; top: 50%; margin-left: -148.5mm; margin-top: -105mm` para escalar desde el centro de la hoja.

## Validacion
- `xmllint` sobre el XML del template y report.
- Actualizacion local del modulo con `docker-compose.local.yml`.

## Limitacion conocida
La confirmacion final debe ser visual, generando el PDF desde Odoo. El factor `1.08` puede requerir ajuste fino.
