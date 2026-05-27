# Changelog 2026-05-22 — Safeguard for date_start_class in welcome emails (ONL batches)

## Resumen
Se implementa una salvaguarda en el envío de correos de bienvenida para lotes de modalidad Online. Si el campo `date_start_class` (Fecha de inicio de clases) en el lote (`op.batch`) está vacío al momento de enviar el correo de bienvenida, este se autopuebla automáticamente con el valor del campo `start_date` (Fecha de inicio del lote) del mismo registro. Esto evita que se envíen plantillas con marcadores de posición vacíos como "Fecha".

## Cambios por módulo

### `addons-extra/addons_uisep/irg_elearning_correo_bienvenida_selector` (16.0.1.0.0)
* **Modelos (`models/op_admission.py`):**
  * Modificación del método `send_mail` para interceptar admisiones de modalidad Online y autopoblar `date_start_class` con `start_date` en el lote correspondiente si se detecta que está vacío antes del envío del correo.
  * Añadida lógica de logs informativos (`_logger.info`) para registrar cuándo se aplica esta autopoblación.
* **Pruebas (`tests/test_welcome_mail.py`):**
  * Creación de la suite de pruebas unitarias `TestWelcomeMailSafeguard` con dos casos de prueba:
    1. `test_send_mail_online_modality_auto_populates_date_start_class`: Verifica la autopoblación de `date_start_class` al detectar la modalidad Online por nombre.
    2. `test_send_mail_online_code_auto_populates_date_start_class`: Verifica la autopoblación de `date_start_class` al detectar la modalidad Online por código de lote ("ONL") incluso tras limpiar el campo directamente.

## Documentación
* Creada la documentación de referencia del módulo en [irg_elearning_correo_bienvenida_selector.md](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/doc/modules/extrairg/irg_elearning_correo_bienvenida_selector.md).

## Pruebas y Validación Local
Las pruebas unitarias se ejecutaron de manera exitosa en el entorno local utilizando la base de datos `test_irg_db` y el contenedor Docker `odoo_latest` (definido en `docker-compose.local.yml`).

### Comando de ejecución de tests:
```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -i irg_elearning_correo_bienvenida_selector \
    --test-enable --stop-after-init --db_host=pgodoo_latest
```

### Resultado de la ejecución:
* **Estado:** Aprobado / Exitoso (Passed)
* **Errores:** 0
* **Fallos (Failures):** 0
* **Casos ejecutados:** 2 de 2 pasados con éxito.
