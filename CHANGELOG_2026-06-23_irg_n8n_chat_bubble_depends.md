# Changelog - 2026-06-23 - Dependencias en irg_n8n_chat_bubble

## Cambios realizados
* **Corrección de Dependencias en el Manifiesto del Módulo (`__manifest__.py`)**:
  - Se agregó `'website'` a la lista de dependencias (`'depends'`) del módulo `irg_n8n_chat_bubble`.
  - Esta dependencia es obligatoria para garantizar el orden de carga correcto del ORM y evitar errores de `External ID not found` cuando las plantillas QWeb del módulo extienden el layout base `website.layout` del portal web.
