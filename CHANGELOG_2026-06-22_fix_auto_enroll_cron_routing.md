# Changelog - 2026-06-22

## Corrección de Enrutamiento en Cron de Auto-inscripción (Auto Enroll)

Se ha corregido un fallo lógico por el cual el cron automático diario `Auto Enroll Students` omitía por completo la inscripción de alumnos de lotes Online (`ONL`) cuando dichos lotes tenían asignaturas con fechas programadas específicas.

### Archivos Modificados:
- **`addons-extra/extrairg/irg_online_subject_opening/models/op_admission.py`**:
  * Se modificó el método `cron_auto_enroll_student` para usar segmentación dinámica en Python mediante `record._irg_has_online_subject_opening_context()`, garantizando que los lotes online con fechas caigan en la lógica estándar del lote.
- **`addons-extra/extrairg/irg_online_subject_opening/tests/test_online_subject_opening.py`**:
  * Se añadió la prueba unitaria `test_cron_auto_enroll_student_with_onl_batch_having_dates` para verificar el correcto funcionamiento del cron ante este escenario.

### Estado de Validación:
- **Validado**: 13 pruebas unitarias ejecutadas con éxito:
  ```bash
  docker compose -f docker-compose.local.yml run --rm odoo_local odoo -c /etc/odoo/odoo.conf -d odoo_test -i irg_online_subject_opening,irg_online_clone_access_fix --test-enable --stop-after-init
  ```
  - **Resultado**: 13 pruebas unitarias superadas, **0 fallos** y **0 errores**.
