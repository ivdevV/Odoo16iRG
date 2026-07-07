# Changelog - Escalado Adaptativo para Nombres de Cursos Largos (07 de Julio de 2026)

## Cambios realizados
En el módulo personalizado `irg_diploma_graduacion_student`:
- **Implementación de escalado tipográfico adaptativo**: En el reporte PDF en formato A3 landscape (`diploma_pdf_report.py`), se reemplazó la maquetación fija de fuente para los nombres del curso por una lógica dinámica que evalúa la división de texto (`simpleSplit` de ReportLab) para evitar solapamientos verticales:
  - **1-2 líneas**: Conserva la tipografía de **32 pt** y el leading de **36 pt** con Y de inicio `510` pt.
  - **3 líneas**: Reduce automáticamente a **24 pt** con leading de **28 pt** y sube la Y de inicio a `525` pt para otorgar más margen vertical.
  - **4+ líneas**: Reduce automáticamente a **20 pt** con leading de **24 pt** y Y de inicio `525` pt.

## Justificación
El título del Máster en Trastornos del Neurodesarrollo y Daño Cerebral Adquirido Infantojuvenil es extremadamente largo (86 caracteres), lo que provocaba que se dividiera en 4 líneas con la fuente estándar de 32 pt y chocara con el conector "a" (Y=430) y el nombre del estudiante (Y=380). El escalado adaptativo garantiza un ajuste visual perfecto para títulos largos sin alterar el diseño de másteres cortos.

## Validación
- Comprobación de sintaxis con `py_compile`.
- Pruebas locales con script de generación para dos escenarios:
  - Máster Largo (Neurodesarrollo): Generado exitosamente en `missions/fix_graduation_diploma_long_title_wrapping/artifacts/diploma_test_long.pdf` con fuente adaptada a 24 pt (3 líneas) sin colisionar con elementos inferiores.
  - Máster Corto (Psicología Clínica): Generado exitosamente en `missions/fix_graduation_diploma_long_title_wrapping/artifacts/diploma_test_short.pdf` manteniendo su tamaño estándar de 32 pt.
