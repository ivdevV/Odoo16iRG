# Misión: Corrección de Enrutamiento en Cron de Auto-inscripción (Auto Enroll Students)

## Alcance
Corregir la lógica de segmentación en el método `cron_auto_enroll_student` de `op.admission` dentro del módulo `irg_online_subject_opening` para garantizar que los alumnos de lotes Online (`ONL`) que tienen fechas planificadas en sus asignaturas sean procesados por la lógica de fechas estándar del lote, en lugar de ser omitidos por completo.

## Clasificación de Complejidad
* **Tier:** `standard`
* **Justificación:** Afecta a un solo archivo de código (`op_admission.py`), pero es una modificación crítica en la sincronización de accesos al e-learning y requiere conocer la herencia y enrutamiento del flujo de admisiones de Odoo.
* **Modelo elegido para la fase:** Gemini 3.5 Flash (High) (Estándar/Intermedio).

## Plan de Ejecución
1. Modificar `addons-extra/extrairg/irg_online_subject_opening/models/op_admission.py` aplicando la segmentación dinámica en Python mediante `_irg_has_online_subject_opening_context()`.
2. Validar ejecutando los tests del módulo para prevenir regresiones.
3. Iniciar Odoo shell en el contenedor para simular el cron de forma manual.
4. Generar `diff.patch`, `execution.log` y `verification.json` para cerrar la misión.
