# Plan de Misión - Excluir Lotes que comienzan por "DI"

## Complejidad de la tarea
* **Tier:** `standard`
* **Justificación:** Requiere modificar la lógica de negocio del módulo `irg_batch_homeclass_api_scheduler` en `op_batch.py` y añadir tests unitarios (`test_op_batch.py`), afectando a 2 archivos de lógica y configuración, y verificando mediante ejecución de tests en el entorno de desarrollo local.
* **Modelo elegido:** Gemini 3.5 Flash (High).

## Alcance
1. Modificar la función `_compute_is_homeclass_batch` en `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/models/op_batch.py` para forzar `is_homeclass_batch = False` si el código del lote (`record.code`) comienza por "DI" (case-insensitive).
2. Crear la suite de tests en `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/tests/test_op_batch.py` para validar ambos casos:
   - Lotes normales que sí deben sincronizarse.
   - Lotes que comienzan por "DI" que deben excluirse.
3. Ejecutar los tests en el entorno Docker local contra la base de datos `odoo16irg_local`.
4. Documentar la solución y emitir la evidencia en `verification.json` con estado `passed`.

## Archivos Afectados
* `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/models/op_batch.py`
* `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/__init__.py`
* `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/tests/__init__.py` [NUEVO]
* `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/tests/test_op_batch.py` [NUEVO]
