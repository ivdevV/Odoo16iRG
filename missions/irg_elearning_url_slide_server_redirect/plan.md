# irg_elearning_url_slide_server_redirect

## Alcance

Hacer que los slides de tipo `URL` redirijan directamente a la URL configurada antes de renderizar cualquier vista/player de Odoo cuando el usuario los clica desde listados, sidebar, fullscreen o navegacion anterior/siguiente.

## Diagnostico

La redireccion JS al renderizar el contenido no garantiza el comportamiento esperado porque el usuario ya entra en la pantalla de Odoo. El requisito es que al clicar el slide URL se navegue directamente al destino, sin embebido ni pantalla intermedia.

No se implementa un redirect incondicional en controller para no saltar restricciones existentes de acceso, lote, prerrequisitos o visibilidad; se modifican los enlaces visibles que Odoo genera cuando el usuario ya tiene acceso.

## Clasificacion de Complejidad

Tier: `standard`.

Justificacion: cambio acotado en assets y QWeb de `website_slides`, con varias superficies de click pero sin cambios de datos ni seguridad.

## Plan

1. Localizar templates y JS de `website_slides` que generan clicks hacia slides.
2. Cambiar href de listados, sidebar y navegacion prev/next para slides URL.
3. Anadir `data-url` al sidebar fullscreen y redirigir desde el handler JS antes de renderizar.
4. Mantener comportamiento nativo para cualquier otro tipo o si falta URL.
5. Validar sintaxis y actualizacion del modulo en Docker local con tests enfocados.

## Criterios de Aceptacion

- Al clicar un slide URL desde el curso, sidebar, fullscreen o navegacion, el navegador sale directamente a la URL destino.
- No se renderiza el slide dentro de Odoo.
- No se abre pestana nueva.
- Documentos, videos y otros tipos mantienen comportamiento nativo.
