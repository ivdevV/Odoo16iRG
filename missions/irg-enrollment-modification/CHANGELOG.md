# Changelog — irg-enrollment-modification

## 16.0.1.0.0 — 2026-09-04

### Añadido

- Módulo nuevo `irg_enrollment_modification` (no se editan addons existentes).
- Botón oscuro «Modificación de matrícula» en la cabecera de `op.student` para el grupo académico.
- Wizard con matrícula de origen obligatoria y cinco cambios independientes (curso, lote, modalidad, año, forma de pago).
- Solicitud `irg.enrollment.change` en estado `submitted` con Word oficial en Actividades. No escribe matrícula ni pago al crear.
- Visto académico: escribe solo los campos marcados en `op.student.course` (y `x_studio_modalidad` en líneas del pedido). Si no hay cambio de pago, cierra con PDF.
- Visto de contabilidad: escribe `sale.order.payment_mode_id` y PDF con Área Financiera.
- Denegar desde enviada no escribe nada. Denegar desde pendiente de finanzas no revierte lo académico ni escribe el pago.
- Reintento de PDF (`pdf_pending`) si LibreOffice falla después de un visto correcto.

### Seguridad

- Grupo `Departamento académico (matrícula)`. Finanzas usa `account.group_account_invoice`.
- `has_group()` en cada acción mutante antes de cualquier `sudo()`.
- `sudo()` solo para writes de matrícula, modalidad de línea y `payment_mode_id`.
- Chatter del estudiante con `sudo()` y `author_id` del operador (el grupo académico no tiene write en `op.student`).
- `_generate_request_docx` no es RPC-público.

### Validación

- 19 tests de módulo, 0 fallos, 0 errores en `docker-compose.local.yml`.
- E2E TestSprite omitido: MCP no registrado en la sesión.

### Limitaciones conocidas

- No captura firma del alumno ni envía email.
- No actualiza Moodle, campus, horario ni facturas ya publicadas.
- La plantilla Word no se rediseña; el relleno va por etiquetas y filas de tabla.
