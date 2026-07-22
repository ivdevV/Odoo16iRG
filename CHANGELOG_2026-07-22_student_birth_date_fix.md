# CHANGELOG - Corrección de Propagación y Salvaguarda de Fecha de Nacimiento (`birth_date`)

## [2026-07-22] - Salvaguarda y Jerarquía de `birth_date` entre Ventas, Admisiones y Estudiantes

### Corregido
- **`isep_admission_from_student_field`**:
  - Eliminado el hardcode de `fields.Date.today()` al crear `op.student` por anticipado en presupuestos donde el alumno difiere del titular. Se utiliza ahora la fecha de nacimiento real `target_partner.birth_date` o `self.birth_date`.
  - Pasado el valor de `birth_date` al crear la admisión (`op.admission`).
  - Evitada la asignación de `'birth_date': False` al crear `op.student` en `submit_form()`, previniendo el borrado de la fecha real en `res.partner`.
- **`isep_elearning_custom`**:
  - Ajustado `submit_form()` para no pasar `'birth_date': False` en el diccionario `details` al crear `op.student` cuando la admisión carece de fecha pero el contacto posee fecha válida.
- **`irg_sale_manual_confirmation_wizard`**:
  - Ajustada la resolución de `default_birth` al crear la admisión para priorizar `admission.partner_id.birth_date` y `self.student_id.birth_date` (el alumno) en lugar de `self.partner_id.birth_date` (el titular) o `'2000-01-01'`.
  - Mejorada la lógica en `submit_form()`, `enroll_student()` y `get_student_vals()` para consultar secuencialmente la admisión, el estudiante y el contacto antes de aplicar el fallback por defecto.
- **`isep_website_sale_custom`**:
  - Ampliado `parse_date()` para aceptar múltiples formatos de fecha (`YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`, `YYYY/MM/DD`).
  - Modificado `partner_vals` para asignar `birth_date` únicamente si se obtuvo un valor parseado válido, evitando escribir `None` en `res.partner`.

### Añadido
- **Suite de Pruebas Unitarias**: Creado `test_birth_date_safeguard.py` en `irg_sale_manual_confirmation_wizard/tests/` con pruebas automatizadas para validar la preservación de la fecha de nacimiento del alumno.
