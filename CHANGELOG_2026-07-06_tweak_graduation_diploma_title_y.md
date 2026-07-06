# Changelog - Ajuste de posición del título del Diploma de Graduación (06 de Julio de 2026)

## Cambios realizados
En el módulo personalizado `irg_diploma_graduacion_student`:
- **Ajuste visual de coordenadas Y del título**: Se bajaron las coordenadas verticales (Y) de los títulos de cabecera bilingües en el reporte PDF en formato A3 landscape (`diploma_pdf_report.py`):
  - Título en Español ("Diploma de Graduación"): Se bajó de la coordenada Y `660` a `620` pt (desplazamiento de 40 pt hacia abajo).
  - Título en Catalán ("Diploma de Graduació"): Se bajó de la coordenada Y `632` a `592` pt (desplazamiento de 40 pt hacia abajo).

## Justificación
El ajuste responde a la petición del usuario para bajar visualmente el título del diploma, de modo que quede a una distancia óptima de la parte superior del lienzo A3 sin interferir con las columnas de nombres de másteres situadas por debajo (cuyo eje Y comienza en `510` pt).

## Validación
- Comprobación de sintaxis y compilación del módulo sin errores mediante `py_compile`.
- Validación mediante script de emulación con mocks de Odoo en VirtualEnv local para generar un archivo PDF de prueba real, comprobando la correcta renderización por ReportLab sin excepciones de lienzo, fuentes o solapamiento.
- Generación de evidencia PDF exitosa de 72KB en la ruta `missions/tweak_graduation_diploma_title_y/artifacts/diploma_test.pdf`.
