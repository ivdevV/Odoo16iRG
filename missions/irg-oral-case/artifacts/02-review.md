# Review de código — irg_oral_case

Revisor: lectura del diff de producto (modelos, wizard, controlador, seguridad, vistas y tests). No se revisa la redacción de `plan.md` ni el changelog.

## Resultado

Sin observaciones bloqueantes.

## Comprobado

- Módulo nuevo en `addons-extra/extrairg/irg_oral_case`. No hay ediciones de módulos existentes ni del core.
- El slide no cambia de categoría. No hay asset que sustituya el fullscreen de `isep_slide_article_custom`.
- `POST /irg/oral_case/submit` es `auth='user'` y `csrf=True`. El partner que se guarda y el que se reenvía salen de la sesión. `create` de un usuario que no es superusuario ni Settings vuelve a forzar `partner_id`.
- El acceso al slide exige matrícula de ese partner o el grupo Faculty, y el slide publicado salvo para Faculty.
- La clave solo se lee de parámetro o entorno y solo sale en la cabecera hacia n8n, con `allow_redirects=False`. Las respuestas pasan por una lista blanca y redactan la clave.
- `app.gradebook.result` se escribe en `action_confirm`, sin sudo, tras `openeducat_core.group_op_faculty` y el checkbox. No se asigna `survey.user_input.result_id`. El envío y el proxy no crean resultados.
- Un alumno no pasa el `write` de `score_ia`, `resumen_ia` y `error_ai`.
- El cron sale si hay una operación de módulos, si `retention_enabled` no está activo o si `retention_days` es 0. El despacho técnico no puede escribir la nota.
- Los tests cubren esos puntos con n8n mockeado. Esta review no los ejecuta: no hay runtime Odoo en la VM.

## No bloqueante

- Un fallo inesperado del controlador se responde `500` `server_error` y no se registra la traza. Cumple el requisito de no filtrar la clave; en un incidente habrá menos contexto.
- El superusuario de Odoo supera `has_group`. La restricción de la nota oficial vale para usuarios reales, que es lo que prueban los tests.
