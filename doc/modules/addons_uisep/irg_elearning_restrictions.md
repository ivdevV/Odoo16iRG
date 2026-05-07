# irg_elearning_restrictions

**Categoría:** addons_uisep
**Versión:** 16.0.1.0.6
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `website_slides`

---

## ¿Qué hace este módulo?

Este módulo añade una capa de control de acceso sobre el eLearning de Odoo para impedir que un alumno consulte determinadas diapositivas antes de haber completado los contenidos definidos como requisito. La restricción se configura directamente en la ficha de la diapositiva, dentro del backend de eLearning, seleccionando qué otras diapositivas del mismo curso deben estar completadas previamente.

Además de los prerrequisitos académicos, el módulo bloquea el acceso a los materiales del campus cuando el contacto asociado al usuario tiene etiquetas administrativas relacionadas con deuda, concretamente etiquetas cuyo nombre contiene `morosidad` o `burofax`. En ese caso se muestra una pantalla informativa y no se entrega el contenido solicitado.

En la vista fullscreen del curso, el sidebar también respeta estas restricciones: las diapositivas con prerrequisitos pendientes se marcan como no accesibles y se elimina el valor de `data-embed-code` para esas entradas. Así se evita exponer enlaces embebidos de documentos o vídeos cuando el alumno todavía no puede acceder al contenido.

## Funcionalidades principales

- Añade el campo de prerrequisitos `restriction_slide_ids` en `slide.slide`.
- Permite configurar, por diapositiva, qué slides del mismo curso deben completarse antes de acceder.
- Bloquea la ruta pública de una diapositiva cuando el usuario autenticado no ha completado todos los requisitos.
- Redirige a login a usuarios públicos que intentan abrir un contenido con prerrequisitos.
- Bloquea el acceso a eLearning para usuarios cuyo partner tenga etiquetas administrativas de morosidad o burofax.
- Muestra páginas específicas para contenido bloqueado por prerrequisitos y por restricción administrativa.
- Inyecta en el contexto fullscreen el conjunto de diapositivas restringidas para el usuario actual.
- Marca en el sidebar fullscreen las diapositivas restringidas como no accesibles.
- Limpia `data-embed-code` en slides restringidos para no exponer URLs embebidas de vídeos, documentos, infografías, contenido externo, Bunny o SCORM.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `slide.slide` | Herencia | `restriction_slide_ids` |

## Vistas y UI

El módulo hereda la vista formulario de `slide.slide` mediante `website_slides.view_slide_slide_form`. Dentro de la pestaña de cuestionario, antes del grupo de recompensas, añade el bloque **Prerrequisitos (iRG)** con el campo `restriction_slide_ids` como etiquetas many2many. El dominio limita la selección a diapositivas del mismo canal y excluye la propia diapositiva.

También añade dos plantillas QWeb públicas:

- `slide_restriction_error`: informa al alumno de que el contenido está bloqueado por prerrequisitos pendientes y lista las diapositivas que debe completar antes de volver al curso.
- `slide_access_blocked`: informa de una restricción administrativa asociada al usuario y solicita contactar con Atención al Alumno.

La plantilla `slide_fullscreen_sidebar_restriction` hereda `website_slides.slide_fullscreen_sidebar_category`. Si una diapositiva está incluida en `restricted_slide_ids`, fuerza `can_access` a `False` y deja `t-att-data-embed-code` en `False`; si no está restringida, conserva el comportamiento estándar de Odoo para categorías embebibles.

## Controladores / Endpoints

| Método | Ruta | Autenticación | Descripción |
|--------|------|---------------|-------------|
| HTTP GET | `/slides/slide/<slide>` | Pública | Extiende la vista de diapositiva de `website_slides` para aplicar bloqueos por deuda administrativa y por prerrequisitos pendientes antes de delegar en el controlador original. |

El controlador también sobrescribe `_get_slide_detail(slide)` para añadir `restricted_slide_ids` al contexto usado por la navegación fullscreen. Ese conjunto se calcula con las diapositivas del canal cuyos prerrequisitos no constan como completados para el partner del usuario actual.

## Dependencias externas

- `website_slides`: aporta los modelos de eLearning (`slide.slide`, `slide.slide.partner`), las rutas públicas de slides y las plantillas fullscreen que este módulo hereda.

## Notas técnicas

- La comprobación de prerrequisitos no se realiza en el método `_check_prerequisite`; el modelo conserva el método como marcador y la lógica efectiva vive en el controlador web para ofrecer una respuesta de usuario más controlada.
- Se usa `sudo()` para consultar `slide.slide.partner` y las diapositivas del canal al calcular completados y restricciones fullscreen. El resultado se limita a IDs necesarios para decidir acceso y renderizado.
- El bloqueo por deuda administrativa compara los nombres de etiquetas del partner en minúsculas y activa la restricción si contienen `morosidad` o `burofax`.
- Para usuarios públicos, `_get_slide_detail` no marca slides restringidos en fullscreen y la ruta directa a una slide con prerrequisitos redirige al login.
- La protección del sidebar no solo oculta el acceso visual: también evita que el atributo `data-embed-code` contenga el código embebido de slides bloqueadas por prerrequisitos pendientes.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_elearning_restrictions \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_elearning_restrictions \
    --stop-after-init --db_host=pgodoo_latest
```