# irg_campus_workshops_portal_customization

## Contexto

El portal del alumno `/campus` (Dashboard) está estructurado en base a herencias sucesivas del perfil del usuario (`website_profile.user_profile_main`). La cadena de herencias es:
1. `isep_website_custom.user_profile_main_custom` (Reemplaza el wrap de `website_profile.user_profile_main` e incluye `isep_website_custom.user_profile_content`).
2. `isep_website_custom_design.custom_user_profile_content_design` (Hereda de `isep_website_custom.user_profile_content` y reemplaza la sección de Programa Académico).

Cualquier adición o sección personalizada en el portal del alumno debe heredar del final de esta cadena (`isep_website_custom_design.custom_user_profile_content_design`) para garantizar que se apliquen todos los parches de diseño y fixes.

## Patrón Aplicado

Para inyectar nuevas secciones en la página del portal (como la sección de "Talleres"):
- Localizar un elemento estable como el t-call a "Aplicaciones" (`isep_website_custom.user_profile_openeducat`).
- Utilizar XPath con posición `before` o `after` para mantener el orden visual deseado.
- Definir un `<style>` tag local autocontenido en la vista XML heredada para los efectos interactivos en el portal (como efectos hover con elevación mediante `transform` y transiciones), evitando de este modo la necesidad de recompilar activos estáticos (SCSS) globales de Odoo 16 y asegurando un despliegue limpio y 100% aislado.

## Gotcha

En Odoo 16, heredar de vistas de portal QWeb de módulos que a su vez reemplazan elementos en cascada requiere especificar el `inherit_id` exacto de la última plantilla intermedia de diseño cargada en el orden de instalación (`isep_website_custom_design.custom_user_profile_content_design`). Si se hereda de la vista raíz (`isep_website_custom.user_profile_content`), la herencia podría fallar en tiempo de ejecución o no mostrarse si la de diseño reemplaza el mismo nodo.
