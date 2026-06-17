# irg_elearning_url_slide

## 1. Titulo Corto

Tipo de contenido URL para eLearning.

## 2. Resumen Objetivo

Anadir una opcion `URL` al campo `Tipo de contenido` de los slides de eLearning para crear contenidos que enlacen a clases o recursos externos.

## 3. Motivo / Justificacion

La funcionalidad nativa y los tipos custom actuales cubren documentos, videos, Bunny, video externo MP4 y Scorm, pero no un tipo generico de enlace. Se implementa mediante un modulo extra para no tocar core ni modulos existentes.

## 4. Alcance Exacto

- Modelo: herencia de `slide.slide`.
- Vistas backend: herencia de `website_slides.view_slide_slide_form`.
- Templates frontend: herencia de `website_slides.slide_content_detailed`, `website_slides.slide_icon` y `website_slides.slide_fullscreen_sidebar_category`.
- Assets frontend: extension del player fullscreen para renderizar categoria `url`.

## 5. Diseno Tecnico

- Modulo: `addons-extra/extrairg/irg_elearning_url_slide`.
- `slide_category`: `selection_add=[('url', 'URL')]`.
- `slide_type`: `selection_add=[('url', 'URL')]` con compute heredado.
- Campos nuevos:
  - `irg_url`: URL destino.
  - `irg_url_button_label`: texto del boton.
- Validacion: `irg_url` obligatorio si `slide_category == 'url'` y esquema `http(s)`.
- Render: tarjeta simple con boton que navega en la misma ventana.

## 6. Dependencias

- `website_slides`
- `website`
- `web`

## 7. Backwards-Compatibility / Migracion

No requiere migracion de datos. El nuevo valor de seleccion solo aplica a contenidos creados despues de instalar el modulo.

## 8. Casos de Prueba / Criterios de Aceptacion

- Instalar/actualizar modulo sin errores.
- Crear slide con `Tipo de contenido = URL`.
- Verificar que URL es obligatoria para ese tipo.
- Verificar que `http://` y `https://` son aceptados.
- Verificar que esquemas no permitidos fallan.
- Verificar render en vista normal y fullscreen.
- Verificar que el enlace se abre en la misma ventana.

## 9. Rollback Plan

Desinstalar el modulo `irg_elearning_url_slide`. Si existen slides con `slide_category = 'url'`, cambiarlos antes a otro tipo compatible o eliminarlos para evitar valores de seleccion inexistentes tras la desinstalacion.

## 10. Estimacion y Responsable

Estimacion: 1 jornada corta incluyendo validacion local.

Responsable: iRG / agente de desarrollo Odoo 16.
