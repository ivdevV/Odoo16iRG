# CHANGELOG — 2026-06-12 — irg_hide_certifies_button

## Nuevo módulo: `addons-extra/extrairg/irg_hide_certifies_button` (16.0.1.0.0)

### Problema

La ficha del estudiante mostraba dos botones de diplomas: "Generar Diploma"
(flujo vigente) y "Certifies / Diplomas" (wizard legacy de
`isep_openeducat_reports`). Solo debe quedar "Generar Diploma".

### Cambios

- Vista heredada que elimina el botón "Certifies / Diplomas" de la cabecera de
  `op.student`. Reversible desinstalando el módulo.

### Pruebas

- 1 test unitario (TDD), `0 failed, 0 error(s)` en Odoo local.

### Despliegue

- Instalar módulo `irg_hide_certifies_button`.
- Nota: requiere PyPDF2 con API moderna en el servidor (ya presente en dev/beta;
  en la imagen local se fijó `PyPDF2==2.12.1`).
