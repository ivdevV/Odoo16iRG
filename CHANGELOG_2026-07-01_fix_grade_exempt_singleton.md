# Changelog: Corrección de Singleton en Helper de Exención de Calificaciones NLEX (`irg_nlex_grade_exemption`)

**Fecha:** 2026-07-01  
**Autor:** Antigravity / Google DeepMind  
**Misión:** `fix_grade_exempt_singleton`

## Descripción del Problema
Al intentar entrar a la libreta de calificaciones de ciertos alumnos, la carga fallaba con el siguiente error:
`ValueError: Expected singleton: op.subject()`
Esto se debía a que el helper `irg_is_grade_exempt()` en `op.subject` utilizaba `self.ensure_one()` de forma incondicional. Cuando se evaluaban líneas de calificaciones obligatorias que tenían el campo de materia (`op_subject_id`) vacío, el método era llamado sobre un recordset vacío, lo que provocaba la caída por singleton.

Adicionalmente, al ejecutar los tests unitarios en el entorno local, se presentaba una caída por un conflicto de selección en el campo `res.partner.gender` debido a valores incompatibles y un valor por defecto no válido (`'male'`). El módulo `irg_admission_gender_fix` resuelve este conflicto globalmente, pero como no estaba declarado como dependencia en `irg_nlex_grade_exemption`, Odoo ejecutaba los tests de este último antes de cargar el fix.

## Cambios Introducidos

### Módulo `irg_nlex_grade_exemption` (v16.0.1.2.1)
- **Helper de Exención (`models/op_subject.py`):**
  - Se modificó `irg_is_grade_exempt()` para retornar `False` inmediatamente si `self` es un recordset vacío, evitando que llame a `ensure_one()`.
- **Manifiesto (`__manifest__.py`):**
  - Se añadió `'irg_admission_gender_fix'` a las dependencias (`depends`) del módulo para asegurar que el fix de géneros se cargue antes y evitar el error `'male'` en la suite de tests.
  - Se incrementó la versión del módulo a `16.0.1.2.1`.
- **Suite de Pruebas (`tests/test_nlex_grade_exemption.py`):**
  - Se añadió un caso de prueba que ejecuta el helper `irg_is_grade_exempt()` sobre un recordset de materias vacío (`self.env['op.subject'].browse()`), garantizando que retorna `False` sin errores.
- **Documentación del Módulo (`doc/modules/extrairg/irg_nlex_grade_exemption.md`):**
  - Se actualizó el archivo de documentación para reflejar los cambios aplicados en la versión `16.0.1.2.1` y documentar la solución y pruebas de singleton.

## Pruebas Realizadas
Se ejecutaron todas las pruebas del módulo de exenciones dentro del entorno local Docker (`odoo16irg_local`):
```bash
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_nlex_grade_exemption --test-enable --test-tags=/irg_nlex_grade_exemption --stop-after-init
```
**Resultado:** Las pruebas compilaron y pasaron con éxito:
`0 failed, 0 error(s) of 3 tests when loading database 'test_irg_db'`
