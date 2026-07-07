# Changelog - Salto de Línea en Catalán para el Máster de Neuropsicología (07 de Julio de 2026)

## Cambios realizados
En el módulo personalizado `irg_diploma_graduacion_student`:
- **Salto de línea forzado en catalán**: En `reports/diploma_pdf_report.py` y `wizard/diploma_graduacion_wizard.py` (`_normalize_catalan_course_name`), se añadió una regla específica para interceptar el nombre del curso de Neuropsicología (en catalán, leído de `name_cat`) e insertar un salto de línea `\n` justo antes de "l'Evidència", "Evidència", "la Evidencia" o "Evidencia".
- **Soporte multilínea en ReportLab**: Se adaptó el motor de dibujo (`generate_diploma_pdf` en `diploma_pdf_report.py`) para segmentar el nombre de cualquier curso por saltos de línea `\n` explícitos antes de aplicar `simpleSplit`, permitiendo que el reporte respete el salto manual y dibuje múltiples líneas adecuadamente.

## Justificación
La separación de texto automática en ReportLab para el Máster en Neuropsicología Clínica en catalán causaba que se dividiera en lugares no deseados. Insertando el salto de línea manual justo antes de "l'Evidència" y procesándolo dinámicamente en ReportLab, se garantiza un corte estético y equilibrado del título del curso en el diploma.

## Validación
- Comprobación de compilación con `py_compile`.
- Validación visual de generación local en `.venv`:
  - PDF Neuropsicología (`diploma_neuropsicologia_line_break.pdf`): Generado exitosamente aplicando el salto de línea manual justo antes de "l'Evidència" sin excepciones de lienzo o fuente.
