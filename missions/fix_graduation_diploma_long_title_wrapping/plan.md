# Misión: Ajustar ajuste de línea de cursos largos en el Diploma de Graduación

## Alcance
Implementar un escalado dinámico del tamaño de fuente y leading de la sección de nombres de cursos en `irg_diploma_graduacion_student` para evitar solapamientos visuales cuando el título de un máster sea muy largo (como ocurre con "Neurodesarrollo", que ocupa 4 líneas a 32 pt).

## Clasificación de Complejidad
- **Tier:** `standard`
- **Justificación:** Requiere agregar lógica de decisión dinámica para evaluar la anchura y número de líneas generadas por `simpleSplit` de ReportLab y adaptar el tamaño de la tipografía y del interlineado. Afecta a un solo archivo de reporte.

## Modelos Asignados
- **Orquestador (Plan):** Gemini 3.5 Flash (actual)
- **Codificador (Implementación):** Gemini 3.5 Flash (gama estándar)
- **Testeador (Validación):** Gemini 3.5 Flash (intermedio)
- **Documentador (Documentación):** Gemini 3.5 Flash (ligero)

## Detalles del Cambio
- Archivo afectado: `addons-extra/extrairg/irg_diploma_graduacion_student/reports/diploma_pdf_report.py`
- Lógica actual:
  - Fija un tamaño de fuente de 32 pt y leading de 36 pt.
- Propuesta adaptativa:
  - Evaluar la cantidad de líneas generadas a 32 pt. Si supera 2 líneas, bajar a 24 pt (con leading 28 pt).
  - Si aún supera las 3 líneas a 24 pt, bajar a 20 pt (con leading 24 pt).
  - Ajustar dinámicamente la posición inicial de dibujo Y para dar más espacio vertical en casos extremos.

## Plan de Validación
- Probar localmente en `.venv` usando un script de emulación de ReportLab que use el máster de Neurodesarrollo y verificar que el PDF se genera con el tamaño de fuente ajustado automáticamente sin solaparse con el conector "a" ni con el estudiante.
- Generar el PDF y verificar visualmente las proporciones.
- Crear `verification.json` correspondiente.
