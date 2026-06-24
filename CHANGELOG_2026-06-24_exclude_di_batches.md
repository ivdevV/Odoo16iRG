# Changelog - 24/06/2026

## Exclusión de Lotes "DI" en Planificador de Calendario HomeClass

### Cambios
- **Modificado** `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/models/op_batch.py`:
  - Se modificó la propiedad computada `_compute_is_homeclass_batch` para verificar si el código del lote comienza con "DI" (case-insensitive). Si es así, se le asigna `is_homeclass_batch = False`, lo que previene que sea considerado como lote HomeClass y aborta la sincronización automática con la API de calendarios CRM.
- **Modificado** `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/__init__.py`:
  - Importado el paquete de tests.
- **Creado** `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/tests/__init__.py`:
  - Definida la importación de tests.
- **Creado** `addons-extra/extrairg/irg_batch_homeclass_api_scheduler/tests/test_op_batch.py`:
  - Desarrollada suite de tests unitarios (`TestOpBatchHomeClass`) cubriendo la lógica de detección, exclusión por prefijo "DI", case-insensitivity y comportamiento tras edición de código (`write`).

### Pruebas Realizadas
- Pruebas unitarias ejecutadas contra `odoo16irg_local` usando `--test-enable`.
- Resultado: **0 fallos, 0 errores en 4 tests**.
- Logs de depuración confirmaron el salto del sync para lotes que empiezan por "DI".
