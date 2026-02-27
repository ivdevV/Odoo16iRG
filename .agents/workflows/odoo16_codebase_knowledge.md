---
description: Consultar reglas de desarrollo y análisis de Odoo 16 en el workspace
---

# Reglas de Odoo y Conocimiento del Proyecto
El usuario ha guardado las convenciones de modificación del código y reportes de análisis en el directorio `.agents/knowledge/` del repositorio actual.

Siempre que el servidor plantee una tarea sobre Odoo o sobre plantillas de correo, o cuando el usuario pida consultarlo bajo un concepto como "revisa las reglas del proyecto", DEBES seguir este paso fundamental:

1. Utiliza la herramienta `view_file` para leer el archivo base de conocimiento:
   `/home/ivrogo/workspace/odoo_local/Odoo16iRG/.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
2. Aplica las directrices como referencia, teniendo en cuenta la estructura estricta (`addons-extra/extrairg/`) y asegurando que las modificaciones respetan el informe de análisis ya realizado sobre `mail.template`.

// turbo
3. **No repitas el análisis de código** para reportar hallazgos de `mail.template` si la información vigente en tu knowledge file te responde la pregunta.
