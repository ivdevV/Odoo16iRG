# Plan de Misión: Modificar Origen de Datos de Identificación en Certificados de Notas

Modificar la obtención del tipo y número de documento de identificación del estudiante en los certificados de notas (tanto el completo `irg_gradebook_certificates` como el parcial `irg_certificate_partial`), de modo que se obtengan del modelo `op.student` (variables `document_type_id` y `document_number`) en lugar de `res.partner`. Se mantendrá un mecanismo de fallback robusto hacia el modelo `res.partner` si el estudiante no tiene estos datos o no se encuentra el registro.

## Clasificación de Complejidad

- **Tier:** `standard`
- **Justificación:** Se modifican entre 2 y 3 archivos (`irg_gradebook_certificates/models/irg_certificate_request.py`, `irg_certificate_partial/models/irg_certificate_request.py` y `irg_gradebook_certificates/report/certificate_templates.xml`). Afecta a lógica localizada con un contexto claro, sin decisiones de arquitectura complejas o riesgos de seguridad/concurrencia.
- **Modelos Asignados:**
  - Orquestador: Gemini 3.5 Flash
  - Implementación: Gemini 3.5 Flash
  - Validación: Gemini 3.5 Flash
  - Documentación: Gemini 3.5 Flash

---

## User Review Required

- Se mantendrá compatibilidad hacia atrás: si `op.student` no tiene asignado `document_type_id` o `document_number`, o si el estudiante no se puede resolver, el sistema usará los campos tradicionales de `res.partner` (`l10n_latam_identification_type_id` y `vat`).
- No se subirá ningún cambio a la rama remota `Dev_iRG` hasta que la validación sea exitosa y el usuario dé su aprobación explícita.

---

## Open Questions

- **Pregunta:** ¿Desea aplicar esta misma modificación al certificado de asistencia (`irg_certificate_attendance`), el cual actualmente también obtiene los datos de `res.partner`?
  *Por defecto, nos limitaremos estrictamente a los dos módulos indicados (`irg_gradebook_certificates` y `irg_certificate_partial`), a menos que nos confirme que prefiere extenderlo a asistencia.*

---

## Proposed Changes

### Módulo `irg_gradebook_certificates`

#### [MODIFY] [irg_certificate_request.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_gradebook_certificates/models/irg_certificate_request.py)
Modificar el método `_fill_template` para recuperar el estudiante (`op.student`) desde `self.gradebook_student_id.student_id` (o buscándolo por `partner_id` si no está enlazado). Asignar `id_label` del campo `student.document_type_id.name` y `documento` del campo `student.document_number`. Aplicar el fallback a `res.partner` si los valores son nulos.

#### [MODIFY] [certificate_templates.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_gradebook_certificates/report/certificate_templates.xml)
Actualizar el QWeb template `report_certificate_document` (líneas 8-10) para obtener el tipo de documento (`id_type_name`) y el número (`id_number`) desde el estudiante con el mismo mecanismo de fallback.

---

### Módulo `irg_certificate_partial`

#### [MODIFY] [irg_certificate_request.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_certificate_partial/models/irg_certificate_request.py)
Modificar el método `_fill_template` de este módulo de forma homóloga al del módulo base para asegurar que los certificados parciales en formato Word (.docx) usen los campos del estudiante con el fallback correspondiente.

---

## Verification Plan

### Automated Tests
- Ejecutar las pruebas unitarias existentes del módulo parcial:
  ```bash
  pytest addons-extra/extrairg/irg_certificate_partial/tests/test_partial.py
  ```
- Añadir un nuevo test unitario en `test_partial.py` para validar específicamente que cuando el estudiante (`op.student`) tiene `document_type_id` y `document_number` definidos, el certificado use esos valores en vez de los de `res.partner`.
- Crear una prueba similar para el módulo base `irg_gradebook_certificates` si es factible.

### Manual Verification
- Comprobar visualmente la generación de los certificados con el entorno local de Docker `docker-compose.local.yml`.
