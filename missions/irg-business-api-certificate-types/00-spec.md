# Spec — certificados adicionales en `irg_business_api`

## Objetivo

Lisa puede generar, con el mismo comando `irg_generate_gradebook_certificate`, los PDFs oficiales de `irg.certificate.request` que el campus ya ofrece: notas (parcial/completo), **diploma**, **asistencia** y **matrícula**. El resultado verificado sigue incluyendo `file_b64` y checksum; el adjunto permanece privado y Odoo no envía correo al alumno.

## Fuera de alcance

- `irg.diplomado.wizard` / `irg.diplomado.registry` (diplomado de curso, producto distinto).
- Actas TFM/TFG (`irg.tfm.acta`): descarga de documentos ya existentes, no generación por este comando.
- Cambiar `irg_gradebook_certificates`, portal o plantillas Word/ReportLab.
- Nuevo código de operación: se conserva el nombre para no romper a Lisa.

## Contrato

`document_type`: `gradebook` | `gradebook_partial` | `diploma` | `attendance` | `enrollment`.

Reglas de libreta (portal):

- `gradebook` y `diploma` exigen `state == done`.
- `gradebook_partial`, `attendance`, `enrollment` se permiten con libreta abierta.

Generación:

- Notas: wizard `irg.certificate.wizard.action_generate()` (sin cambio).
- Diploma, matrícula, asistencia: `irg.certificate.request` con `origin=backend`, `state=done`, `_generate_and_attach_pdf()`, `action_download_pdf()`.
- Asistencia: `session_id` obligatorio si el campo existe (`irg_certificate_attendance`). El modelo oficial valida HomeClass / lote HC.
- `session_id` no se admite en los demás tipos.

## Criterios de aceptación

1. Enrollment en libreta abierta: preview + approve con PDF privado.
2. Diploma en libreta abierta: error; en `done`: PDF.
3. Asistencia sin `session_id`: error (si el módulo está instalado).
4. Notas parciales siguen usando el wizard.
5. Sin mail, sin `public=True`, sin factura portal.
