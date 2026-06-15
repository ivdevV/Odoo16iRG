# irg_elearning_url_slide_direct_redirect

## Alcance

Cambiar el comportamiento de los slides de tipo `URL` en el reproductor fullscreen de eLearning para que al seleccionarlos redirijan directamente a la URL configurada, evitando la pantalla intermedia.

## Diagnostico

Actualmente el modulo renderiza un contenido intermedio mediante `embed_code`. En fullscreen esto muestra una pantalla vacia/intermedia antes de que el usuario pulse el enlace. El requisito actualizado es que el click sobre el contenido URL lleve directamente al destino.

## Clasificacion de Complejidad

Tier: `trivial`.

Justificacion: cambio localizado en el asset JS del modulo, sin cambios de datos, seguridad, autenticacion, concurrencia ni despliegue.

## Plan

1. Extraer la URL destino desde el `embedCode` ya disponible en los datos del slide.
2. En `_renderSlide`, si la categoria es `url`, redirigir `window.location.href` a esa URL.
3. Mantener fallback al render actual si no se puede extraer una URL.
4. Validar sintaxis JS/Python/XML y actualizar el modulo en Docker local.

## Criterios de Aceptacion

- Al clicar un slide `URL` en fullscreen, el navegador navega directamente a la URL configurada.
- No se abre pestana nueva.
- Si falta la URL, no rompe el reproductor y usa el render actual.
