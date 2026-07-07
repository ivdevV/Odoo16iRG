# Changelog - Restricción Exclusiva de Fuente para el Máster de Neurodesarrollo (07 de Julio de 2026)

## Cambios realizados
En el módulo personalizado `irg_diploma_graduacion_student`:
- **Corrección de regresión tipográfica**: Se eliminó la lógica de escalado dinámico general y se implementó una condición lógica específica (`"Neurodesarrollo" in course_name_es`) en el reporte PDF en formato A3 landscape (`diploma_pdf_report.py`):
  - **Máster de Neurodesarrollo (Español / Catalán)**: Se escala automáticamente a **24 pt** (leading de **28 pt** y Y de inicio `525` pt) para que quepa en 3 líneas limpiamente sin solapamiento central.
  - **Todos los demás másteres** (incluyendo **Neuropsicología Clínica basada en la Evidencia** y otros): Mantienen sin alterar su tamaño de fuente corporativo original de **32 pt** (leading de **36 pt** y origen Y en `510` pt) como estaba especificado originalmente.

## Justificación
La lógica adaptativa genérica previa había causado una regresión en el Máster de Neuropsicología Clínica (haciendo que su fuente se redujera a 24 pt por ser un título largo). Este cambio garantiza que la reducción de tamaño de letra de curso se aplique única y exclusivamente al Máster de Neurodesarrollo, que es el único que presenta el problema de 4 líneas y solapamiento visual directo.

## Validación
- Comprobación de compilación con `py_compile`.
- Validación visual de generación local en `.venv`:
  - PDF Neurodesarrollo (`diploma_neurodesarrollo.pdf`): Correctamente a 24 pt.
  - PDF Neuropsicología Clínica (`diploma_neuropsicologia.pdf`): Correctamente a 32 pt (sin regresión).
