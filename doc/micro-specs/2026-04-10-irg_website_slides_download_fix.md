# Micro-spec: Fix descarga PDF en slides e-learning

## Título
Corregir el botón de descarga PDF en website slides para evitar TypeError cuando el contenido no tiene `.oe_structure`.

## Resumen objetivo
Implementar un parche local IRG que evite el error JavaScript `undefined is not an object (evaluating 'content.children('.oe_structure')[0].cloneNode')` en el botón de descarga de slides y proporcione un fallback seguro cuando la estructura de contenido de la lección sea diferente.

## Motivo / justificación
- El bug impacta a alumnos que descargan o visualizan contenido didáctico en slides de e-learning.
- El script actual en `website_slides_customizations/static/src/frontend/download.js` asume que `.o_wslides_lesson_content` siempre contiene un hijo `.oe_structure` y un árbol fijo de slides.
- En casos de contenido embebido, artículos o presentaciones no estándar, esa suposición falla y lanza un TypeError.

## Alcance exacto
- Módulo nuevo bajo `addons-extra/extrairg/irg_website_slides_download_fix/`.
- Actúa solo en frontend mediante un asset JS que parchea la función global de descarga.
- No se modifican módulos nativos ni el código de `addons_uisep`.
- No cambia datos de base de datos.

## Diseño técnico
- Crear un asset JS que registre un listener de click en `#custom_download_button` en captura.
- Evitar que el handler inline anterior ejecute el código vulnerable.
- Reemplazar la selección insegura de `.oe_structure`/`slides` con selectores `querySelector` / `querySelectorAll` y fallback al contenido visible.
- Limpiar scripts del HTML clonado antes de enviar a `html2pdf`.
- Restaurar el estado del botón si la generación de PDF falla.

## Dependencias
- `website_slides`
- `website`
- `web`

## Backwards-compatibility / migración
- Compatible con instalaciones existentes.
- Si el módulo se desinstala, vuelve al comportamiento actual de descarga de `website_slides_customizations`.
- No hay impacto en datos.

## Casos de prueba / criterios de aceptación
1. Usuario abre slide con contenido estándar y hace click en Descargar.
   - [ ] Se inicia la descarga sin TypeError.
2. Usuario abre slide de encuesta o contenido HTML embebido sin `.oe_structure`.
   - [ ] No ocurre error de JavaScript.
   - [ ] El botón vuelve a estado normal si la descarga falla.
3. Usuario accede a vista fullscreen con `fullscreen=1`.
   - [ ] Se usa `.o_wslides_fs_content` como fuente cuando existe.
4. Usuario usa botón en el template de contenido detallado.
   - [ ] El fallback construye un contenedor válido cuando no hay encabezados.

## Rollback plan
- Desinstalar el módulo `irg_website_slides_download_fix` desde la UI de Apps o con `-u` y `--uninstall`.
- Limpiar caché de assets y navegador.

## Estimación y responsable
- Estimación: 1 hora.
- Responsable: Sebastian.
- Prioridad: Alta (bug de experiencia de usuario en e-learning).

---

## Implementación checklist
- [ ] Crear módulo `irg_website_slides_download_fix` en `addons-extra/extrairg/`
- [ ] Añadir `web.assets_frontend` con el JS de parche
- [ ] Validar que no depende de la estructura exacta de `website_slides`
- [ ] Probar click de descarga en slides estándar y embebidos
- [ ] Añadir changelog corto
