# Misión: Limitar reducción de fuente exclusivamente al Máster de Neurodesarrollo

## Alcance
Corregir la regresión introducida por la lógica adaptativa general que afectó al Máster de Neuropsicología Clínica (haciendo su fuente más pequeña). Modificar la lógica para aplicar la reducción de tamaño de fuente (de 32 pt a 24 pt) y el cambio en la posición de inicio Y **únicamente** cuando se trate del Máster de Neurodesarrollo. Todos los demás másteres (incluyendo Neuropsicología Clínica) conservarán sus especificaciones estándar de 32 pt (leading de 36 pt) y origen Y de `510` pt.

## Clasificación de Complejidad
- **Tier:** `trivial`
- **Justificación:** Cambio de una condición lógica simple en un único archivo de reporte. Sin riesgos colaterales.

## Modelos Asignados
- **Orquestador (Plan):** Gemini 3.5 Flash (actual)
- **Codificador (Implementación):** Gemini 3.5 Flash (gama estándar)
- **Testeador (Validación):** Gemini 3.5 Flash (intermedio)
- **Documentador (Documentación):** Gemini 3.5 Flash (ligero)

## Detalles del Cambio
- Archivo afectado: `addons-extra/extrairg/irg_diploma_graduacion_student/reports/diploma_pdf_report.py`
- Lógica en la sección de nombres de curso:
```python
        # Lógica de tamaño de fuente e interlineado (estándar)
        font_size = 32
        leading = 36
        curr_y_start = 510
        
        # Reducción exclusiva y selectiva únicamente para el Máster de Neurodesarrollo
        if "Neurodesarrollo" in course_name_es:
            font_size = 24
            leading = 28
            curr_y_start = 525
```

## Plan de Validación
- Ejecutar compilación con `py_compile`.
- Probar localmente en `.venv` usando un script de generación de PDF simulando:
  - Máster de Neurodesarrollo (validando que se renderiza a 24 pt).
  - Máster en Neuropsicología Clínica (validando que se mantiene a 32 pt).
- Crear `verification.json` correspondiente.
