# Changelog - 2026-05-28

## Cambios en el intervalo de asignaturas online (de 25 a 30 días)

Se ha modificado la lógica de asignación automática de fechas para asignaturas en lotes académicos online, incrementando el intervalo de 25 a 30 días para asegurar consistencia con el flujo del negocio.

### Archivos Modificados:
- **`addons-extra/addons_uisep/isep_elearning_custom/models/op_batch.py`**:
  - Se modificó la línea 34 en el método `_schedule_onl_subjects` para incrementar el intervalo de programación consecutiva de asignaturas online de 25 días a 30 días.

### Archivos Añadidos:
- **`addons-extra/addons_uisep/isep_elearning_custom/tests/test_op_batch.py`**:
  - Contiene las pruebas unitarias para el modelo `op.batch`, comprobando:
    - Programación con separación de 30 días en lotes online.
    - Exclusión de lotes no online de la programación automática.
    - Reprogramación tras la edición de la fecha de inicio (`start_date`) de un lote online.

### Estado de Validación:
- **Validado**: Los tests unitarios han sido ejecutados localmente en Docker:
  ```bash
  docker compose -f docker-compose.local.yml run --rm odoo_local odoo -c /etc/odoo/odoo.conf -d odoo_test -i isep_elearning_custom,isep_student_migration --test-enable --stop-after-init
  ```
  - **Resultado**: 25 tests ejecutados en total (incluyendo 5 tests para `isep_elearning_custom`), con **0 fallos** y **0 errores**.
