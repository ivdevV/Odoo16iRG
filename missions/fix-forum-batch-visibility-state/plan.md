# Misión: Corrección de Campo Inexistente 'state' en Lotes de Foro

## Alcance
Corregir el error `ValueError: Invalid field op.batch.state` en el método `_onchange_irg_course_id` de `forum.forum` reemplazando la condición incorrecta por el campo booleano `active` de Odoo.

## Clasificación de Complejidad
* **Tier:** `trivial`
* **Justificación:** Afecta a un solo archivo de código (`forum_forum.py`), corrige una sola línea de dominio, sin riesgos colaterales ni cambios en modelo de datos.
* **Modelo elegido para la fase:** Gemini 3.5 Flash (High).

## Plan de Ejecución
1. Modificar `addons-extra/extrairg/irg_forum_batch_visibility/models/forum_forum.py` cambiando `('state', '=', 'active')` por `('active', '=', True)`.
2. Validar sintaxis y comportamiento del dominio en la shell de Odoo.
3. Generar `diff.patch`, `execution.log` y `verification.json`.
