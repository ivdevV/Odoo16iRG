# Misión: Salto de línea manual antes de 'Evidencia' en Catalán para Neuropsicología

## Alcance
Forzar un salto de línea (`\n`) en el nombre en catalán (obtenido de la variable `name_cat` del curso) justo antes de la palabra "Evidencia" (o "l'Evidència") para el Máster de Neuropsicología Clínica, adaptando el generador de PDF de ReportLab para procesar saltos de línea explícitos (`\n`). Las traducciones de textos al catalán se manejan desde la variable `name_cat` del curso en Odoo.

## Clasificación de Complejidad
- **Tier:** `standard`
- **Justificación:** Requiere adaptar la lógica de dibujo de ReportLab para iterar sobre sub-líneas (separando por `\n`) antes de realizar la división automática (`simpleSplit`) en `diploma_pdf_report.py`.

## Modelos Asignados
- **Orquestador (Plan):** Gemini 3.5 Flash (actual)
- **Codificador (Implementación):** Gemini 3.5 Flash (gama estándar)
- **Testeador (Validación):** Gemini 3.5 Flash (intermedio)
- **Documentador (Documentación):** Gemini 3.5 Flash (ligero)

## Detalles del Cambio
- **En `reports/diploma_pdf_report.py` y `wizard/diploma_graduacion_wizard.py` (`_normalize_catalan_course_name`)**:
  - Buscar la palabra clave de Neuropsicología y, si está presente, insertar un salto de línea `\n` justo antes de "l'Evidència", "l'evidència", "Evidència", "la Evidencia" o "Evidencia".
- **En `reports/diploma_pdf_report.py` (`generate_diploma_pdf`)**:
  - Modificar la división de texto para que soporte saltos de línea explícitos:
  ```python
  lines_course_cat = []
  for part in course_name_cat.split('\n'):
      lines_course_cat.extend(simpleSplit(part, font_bold, font_size, 450))
      
  lines_course_es = []
  for part in course_name_es.split('\n'):
      lines_course_es.extend(simpleSplit(part, font_bold, font_size, 450))
  ```

## Plan de Validación
- Compilar con `py_compile`.
- Probar localmente en `.venv` usando un script que emule la generación del PDF con el nombre del Máster de Neuropsicología en catalán y validar visualmente que se realiza el salto de línea de forma exacta en "l'Evidència".
