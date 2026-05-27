# Changelog 2026-05-22 — Safeguard for portal user creation on budget confirmation

## Resumen
Se implementa una salvaguarda en el proceso de matriculación (`enroll_student`) de OpenEduCat para asegurar que los estudiantes pre-creados (o existentes) que no dispongan de un usuario de portal (`res.users`) reciban uno de manera automática y consistente. Esto corrige un fallo donde los alumnos matriculados manualmente o mediante e-commerce que eran pre-creados en base de datos antes de la confirmación terminaban sin usuario portal vinculado.

## Cambios por módulo

### `addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard` (16.0.1.0.0)
* **Modelos (`models/op_admission.py`):**
  - Implementación del método helper `_ensure_portal_user()` que analiza la admisión, el estudiante y el partner, verificando si ya existe un usuario de portal o creándolo si fuera necesario.
  - Gestión de colisiones de login: si el email ya existe asociado a otro partner, se unifica el partner en los registros de admisión y de estudiante para evitar fallos por restricción única en Odoo.
  - Sobreescritura del método `enroll_student()` para invocar automáticamente la salvaguarda de usuario antes de procesar el registro del alumno.
* **Pruebas (`tests/test_portal_user.py`):**
  - Creación de la suite de pruebas unitarias `TestPortalUserSafeguard` con tres casos de prueba:
    1. `test_enroll_student_creates_portal_user_if_missing`: Verifica la creación y vinculación automática del usuario portal para un estudiante preexistente sin usuario.
    2. `test_enroll_student_links_existing_portal_user`: Verifica la vinculación de un usuario portal preexistente del partner al estudiante si este no estaba formalmente enlazado.
    3. `test_enroll_student_handles_duplicate_login`: Verifica que ante colisiones de email/login con otro partner, se unifique correctamente la relación en lugar de provocar un error de clave duplicada.

## Documentación
* Creada la documentación de referencia del módulo en [irg_sale_manual_confirmation_wizard.md](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/doc/modules/extrairg/irg_sale_manual_confirmation_wizard.md).

## Pruebas y Validación Local
Las pruebas unitarias del módulo se ejecutaron de manera exitosa en el entorno local utilizando la base de datos `test_irg_db` y el contenedor Docker `odoo16irg_local`.

### Comando de ejecución de tests:
```bash
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -u irg_sale_manual_confirmation_wizard \
    --test-enable --stop-after-init
```

### Resultado de la ejecución:
* **Estado:** Aprobado / Exitoso (Passed)
* **Errores:** 0
* **Fallos (Failures):** 0
* **Casos ejecutados:** 3 de 3 pasados con éxito.
