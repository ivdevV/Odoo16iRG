# irg_online_clone_access_fix

## Objetivo

Corrige el acceso de alumnos Online a asignaturas cuyo canal HomeClass tiene un canal Online clonado independiente.

## Cambios

- Añade `op.subject.irg_get_effective_slide_channel(partner=None, admission=None)` para devolver el canal Online clonado cuando la admision/lote del alumno es Online y el clon existe.
- Extiende la sincronizacion de `irg_online_subject_opening` para buscar y crear `slide.channel.partner` sobre el canal efectivo, no siempre sobre el canal HomeClass.
- Extiende la sincronizacion HomeClass -> Online de `slide.channel.partner` para copiar campos academicos opcionales si existen.
- Hereda la plantilla del portal de `irg_subject_fix` y usa el canal efectivo al calcular `slide_id` y el estado clicable de tarjetas de asignatura.
- Corrige el bootstrap HomeClass -> Online de `irg_course_convocatorias_v2` para copiar campos binarios de documentos (`datas`, `document_binary_content`, nombre de fichero e imagen) y evitar copiar `embed_code`, que puede recalcularse y fallar fuera de una request HTTP.
- Añade la accion backend `Reparar documentos Online` en el canal HomeClass para rellenar binarios faltantes en contenidos Online ya duplicados.

## Uso

1. Instalar o actualizar el modulo `irg_online_clone_access_fix`.
2. Duplicar contenidos desde el canal HomeClass con la accion existente de `irg_course_convocatorias_v2`.
3. Ejecutar la autoinscripcion o el cron habitual si hay alumnos ya matriculados.
4. Verificar en el portal que la tarjeta de la asignatura Online apunta al canal clonado y que los documentos duplicados abren/descargan correctamente.

## Reparar Duplicados Existentes

Para contenidos Online ya creados antes del fix:

1. Abrir el canal HomeClass original.
2. Ir a la pestaña `Online`.
3. Pulsar `Reparar documentos Online`.
4. Revisar la notificacion con el numero de slides reparados.

La accion solo copia binarios faltantes desde el slide original al clon Online relacionado por `irg_original_slide_id`. No vuelve a duplicar slides y no sobrescribe documentos que ya existan en Online.

## Criterios De Comprobacion

- El slide duplicado conserva `irg_original_slide_id` apuntando al original.
- Los documentos duplicados conservan `document_binary_content` o `datas`, segun el campo disponible en la instancia.
- La accion `Reparar documentos Online` rellena documentos faltantes en clones existentes sin crear duplicados nuevos.
- El alumno Online tiene `slide.channel.partner` activo en el canal Online clonado.
- La tarjeta del campus usa el canal efectivo Online y no queda deshabilitada por falta de membresia.

## Validacion

- Tests incluidos en `tests/test_online_clone_access_fix.py` para canal efectivo, sincronizacion de membresia Online y copia de `document_binary_content` en el bootstrap.
- Ejecutado en Odoo local con `docker-compose.local.yml` sobre `test_irg_db`: `0 failed, 0 errors`.

## Limitaciones

- No modifica controladores de acceso de otros modulos; se centra en tarjetas de portal, sincronizacion de membresias y campos copiados por el bootstrap.
- La deteccion de alumno Online usa `_irg_has_online_subject_opening_context()` si existe y, como fallback, el codigo de lote con `ONL` excluyendo `MONL`.
- La reparacion de duplicados existentes requiere que el clon conserve `irg_original_slide_id`; si un contenido Online fue creado manualmente sin enlace al original, no se puede inferir de forma segura que documento copiar.

## Changelog

- `16.0.1.0.0`: modulo inicial para resolver tarjetas no clicables tras clonar contenido HomeClass a Online y restaurar la copia de documentos/binarios en el bootstrap v2.
