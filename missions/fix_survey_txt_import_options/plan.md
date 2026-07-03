# Plan - fix_survey_txt_import_options

## Alcance y descripción
El objetivo de esta misión es corregir el wizard de importación de preguntas tipo test desde archivos de texto (`irg.survey.txt.import.wizard`) para que admita preguntas con un número variable de opciones (por ejemplo, A, B, C en lugar de exigir estrictamente A, B, C, D).

Actualmente el código tiene validaciones fijas para las opciones `A`, `B`, `C` y `D`. Si un bloque de texto en el archivo importado no contiene la clave `D`, se produce un error de validación indicando que falta el campo obligatorio `D`.

## Clasificación de complejidad
- **Complejidad**: `standard`
- **Justificación**: Afecta a un solo archivo de código (`survey_txt_import_wizard.py`), pero implica modificar la lógica de validación, renderizado de previsualización y creación de registros en Odoo, además de agregar tests unitarios para verificar el comportamiento. No afecta seguridad, concurrencia, ni datos históricos críticos.
- **Modelos elegidos**:
  - Plan: Gemini 3.5 Flash (High) (Orquestador)
  - Implementación: Gemini 3.5 Flash (High) (Codificador)
  - Validación: Gemini 3.5 Flash (High) (Testeador)
  - Documentación: Gemini 3.5 Flash (High) (Documentador)

## Cambios Propuestos

### Componente: irg_survey_txt_import_feedback

#### [MODIFY] [survey_txt_import_wizard.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_survey_txt_import_feedback/wizard/survey_txt_import_wizard.py)
- Modificar `_parse_file` para:
  - Definir las claves obligatorias base como `{'P', 'RC'}`.
  - Extraer dinámicamente las claves de opciones como cualquier clave en mayúsculas de longitud 1 excepto `'P'` (por ejemplo, `'A'`, `'B'`, `'C'`, etc.).
  - Validar que las opciones sean consecutivas empezando desde `'A'`.
  - Validar que la respuesta correcta (`RC`) coincida con una de las opciones extraídas.
- Modificar `action_preview` para recorrer y renderizar de forma dinámica las opciones disponibles en cada pregunta en lugar de asumir `'A'`, `'B'`, `'C'`, `'D'`.
- Modificar `action_import` para crear en la base de datos las opciones que realmente contenga la pregunta procesada, en lugar del bucle fijo de `'A'` a `'D'`.

#### [NEW] [__init__.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_survey_txt_import_feedback/tests/__init__.py)
- Importar el archivo de pruebas `test_survey_txt_import`.

#### [NEW] [test_survey_txt_import.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_survey_txt_import_feedback/tests/test_survey_txt_import.py)
- Definir casos de prueba unitarios para verificar:
  - Importación exitosa de preguntas con 4 opciones (A, B, C, D).
  - Importación exitosa de preguntas con 3 opciones (A, B, C).
  - Importación exitosa de preguntas con 5 opciones (A, B, C, D, E).
  - Manejo adecuado de errores de formato (opciones no consecutivas, falta de P o RC, RC no válida, etc.).

## Plan de Verificación

### Pruebas Automatizadas
- Ejecutar los tests en el entorno Docker local con:
  ```bash
  docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_survey_txt_import_feedback --test-enable --test-tags /irg_survey_txt_import_feedback --stop-after-init --log-level=test
  ```

### Verificación Manual
- Subir a la interfaz un archivo `.txt` con preguntas que solo tengan A, B, C y verificar la vista previa y la importación correcta.
