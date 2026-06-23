# Plan de Misión: Corrección de Mapeo de Género en Admisiones

## Alcance
Implementar un nuevo módulo Odoo 16 (`irg_admission_gender_fix`) que herede `op.admission` y `op.student` para interceptar la creación/edición de registros y mapear correctamente los valores de género del contacto (`res.partner`) hacia los valores esperados (`'m'`, `'f'`, `'o'`).
Adicionalmente, incorporar un algoritmo de adivinación inteligente de género basado en el nombre y título del contacto cuando el género no esté explícitamente configurado.

## Clasificación de Complejidad
- **Tier:** `standard`
- **Justificación:** Se introduce un módulo custom nuevo y algoritmos locales basados en heurística de nombres y títulos de contacto. No hay impacto en seguridad ni datos críticos.
- **Modelos Elegidos:**
  - Plan/Orquestación: Gemini 3.5 Pro
  - Codificación/Validación: Gemini 3.5 Flash

## Descomposición del Trabajo
1. Crear el micro-spec `doc/micro-specs/2026-06-21-irg_admission_gender_fix.md`.
2. Crear la estructura del módulo `irg_admission_gender_fix` en `addons-extra/extrairg/`.
3. Implementar la lógica de herencia de `op.admission` y `op.student` para conversión y adivinación de género.
4. Implementar los tests unitarios en `tests/test_gender_mapping.py` incluyendo los casos de adivinación.
5. Ejecutar la suite de tests en el entorno Docker Compose local.
6. Generar el reporte de verificación `verification.json`, el parche `diff.patch` y el log de ejecución `execution.log`.
