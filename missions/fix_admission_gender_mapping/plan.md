# Plan de Misión: Corrección de Mapeo de Género en Admisiones

## Alcance
Implementar un nuevo módulo Odoo 16 (`irg_admission_gender_fix`) que herede `op.admission` y `op.student` para interceptar la creación/edición de registros y mapear correctamente los valores de género del contacto (`res.partner`) hacia los valores esperados (`'m'`, `'f'`, `'o'`).

## Clasificación de Complejidad
- **Tier:** `standard`
- **Justificación:** Se introduce un módulo custom nuevo (5 archivos de código Python/manifiesto) y pruebas unitarias sin impacto en seguridad, concurrencia ni borrado de datos históricos.
- **Modelos Elegidos:**
  - Plan: Gemini 3.5 Pro (Razonamiento)
  - Codificación/Implementación: Gemini 3.5 Flash
  - Validación: Gemini 3.5 Flash
  - Documentación: Gemini 3.5 Flash

## Descomposición del Trabajo
1. Crear el micro-spec `doc/micro-specs/2026-06-21-irg_admission_gender_fix.md`.
2. Crear la estructura del módulo `irg_admission_gender_fix` en `addons-extra/extrairg/`.
3. Implementar la lógica de herencia de `op.admission` y `op.student` para conversión de género.
4. Implementar los tests unitarios en `tests/test_gender_mapping.py`.
5. Ejecutar la suite de tests en el entorno Docker Compose local.
6. Generar el reporte de verificación `verification.json` y el log de ejecución `execution.log`.
