# Changelog - 2026-07-03

## Soporte para Opciones Variables en Importación de Exámenes desde TXT

Se ha corregido el comportamiento del importador de preguntas desde archivos de texto (`irg.survey.txt.import.wizard`) para que no exija obligatoriamente que todas las preguntas tengan exactamente 4 opciones (A, B, C, D). Ahora el sistema permite un número variable de opciones por pregunta (como A, B, C o A, B, C, D, E).

### Archivos Modificados:
- **`addons-extra/extrairg/irg_survey_txt_import_feedback/wizard/survey_txt_import_wizard.py`**:
  * Se modificó `_parse_file()` para extraer de manera dinámica todas las opciones en mayúsculas de una sola letra (excluyendo la clave `'P'`).
  * Se agregó validación para asegurar que las opciones encontradas sean consecutivas y comiencen con la letra `'A'`.
  * Se agregó validación para que la respuesta correcta (`RC`) esté contenida dentro de las opciones detectadas.
  * Se modificaron `action_preview()` y `action_import()` para iterar y procesar de forma dinámica las opciones de cada pregunta en lugar de usar un bucle estático `'A'` a `'D'`.

### Archivos Creados:
- **`addons-extra/extrairg/irg_survey_txt_import_feedback/tests/__init__.py`**:
  * Archivo de inicialización del paquete de pruebas.
- **`addons-extra/extrairg/irg_survey_txt_import_feedback/tests/test_survey_txt_import.py`**:
  * Archivo con 10 pruebas unitarias que cubren casos exitosos de importación de 3, 4 y 5 opciones, previsualización correcta, creación de registros en Odoo y validaciones de errores de formato o consistencia.

### Estado de Validación:
- **Validado**: 10 pruebas unitarias ejecutadas con éxito en el contenedor docker local:
  ```bash
  docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_survey_txt_import_feedback --test-enable --test-tags /irg_survey_txt_import_feedback --stop-after-init --log-level=test
  ```
  - **Resultado**: 10 pruebas unitarias superadas, **0 fallos** y **0 errores**.
