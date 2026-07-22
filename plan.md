# Plan: Corrección de la Propagación y Salvaguarda de la Fecha de Nacimiento (`birth_date`)

## Alcance y Clasificación
- **Nivel de Misión**: `standard` (Cambios acotados en 4 módulos: `isep_admission_from_student_field`, `isep_elearning_custom`, `irg_sale_manual_confirmation_wizard`, `isep_website_sale_custom`).
- **Capacidad Requerida**: Standard (Lógica Odoo ORM, propagación de datos entre presupuesto, admisión, estudiante y partner).

## Criterios de Aceptación
1. **No sobreescritura con la fecha de hoy**: Al confirmar un presupuesto con alumno distinto del titular (`isep_admission_from_student_field`), `op.student` y `op.admission` deben recibir la fecha de nacimiento real del alumno (`target_partner.birth_date` o `self.birth_date`) y NUNCA `fields.Date.today()`.
2. **No borrado de fecha existente (`False`)**: Al ejecutar `submit_form()` en `isep_elearning_custom` e `isep_admission_from_student_field`, no se debe enviar `'birth_date': False` al crear/actualizar `op.student` si la admisión no tiene fecha pero el contacto de `res.partner` sí la tiene.
3. **Búsqueda correcta del alumno en el Wizard Manual**: En `irg_sale_manual_confirmation_wizard`, la búsqueda de fecha por defecto debe priorizar `admission.partner_id.birth_date` / `self.student_id.birth_date` antes que `self.partner_id.birth_date` (el titular) o `'2000-01-01'`.
4. **Soporte de múltiples formatos de fecha en la Web**: `isep_website_sale_custom` debe parsear fechas en formatos `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`, evitando que un formato no-slash convierta la fecha a `False`.
5. **Pruebas Automatizadas**: Crear/ejecutar tests unitarios que certifiquen el comportamiento GREEN.

## Matriz de Roles
- **Orquestador**: Planificación, control del ciclo de vida y gates.
- **Codificador**: Implementación TDD / salvaguardas en los 4 módulos.
- **Revisor**: Revisión de código diff y ausencia de regresiones.
- **Validador**: Ejecución de suite de tests unitarios y emisión de `verification.json`.
- **Documentador**: Actualización de changelog y `execution.md`.
- **Responsable de Entrega**: Notificación final al usuario.

## Fases del Ciclo de Vida
1. **Plan**: `plan.md` e `implementation_plan.md` aprobados.
2. **Implementación/TDD**:
   - Escribir/ejecutar tests unitarios para verificar fallos (RED) y soluciones (GREEN).
   - Aplicar correcciones en los 4 módulos.
3. **Review de Código**: Inspección de diffs y verificación de alcance.
4. **Validación**: Ejecución de suite de pruebas unitarias y generación de `verification.json`.
5. **Documentación**: Actualizar `execution.md` y `CHANGELOG_2026-07-22_student_birth_date_fix.md`.
6. **Publicación Autorizada**: Informar al usuario de la finalización.
