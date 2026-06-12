# irg_hide_certifies_button

**Versión:** 16.0.1.0.0
**Dependencias:** `isep_openeducat_reports`

## Problema

La ficha del estudiante (`op.student`) mostraba dos botones de diplomas en la
cabecera: "Generar Diploma" (flujo vigente, módulo `irg_generacion_diplomas`) y
"Certifies / Diplomas" (wizard legacy de `isep_openeducat_reports`, definido en
`addons-extra/addons_uisep/isep_openeducat_reports/views/op_student_view.xml`).
Solo debe quedar "Generar Diploma".

## Solución

Vista heredada de `isep_openeducat_reports.view_op_student_form_extended` que
elimina el botón vía xpath sobre el `name` de la acción
(`%(isep_openeducat_reports.diplomas_certifies_wizard)d`). Odoo no permite usar
`string` como selector de herencia.

No se toca el módulo legacy: desinstalar este módulo restaura el botón.

## Uso

Instalar el módulo. El botón "Certifies / Diplomas" desaparece de la ficha del
estudiante; el wizard legacy sigue existiendo (accesible por acción directa si
hiciera falta).

## Tests

`tests/test_hide_button.py` (1 test): la vista combinada de `op.student` no
contiene "Certifies / Diplomas".

Ejecutado en Odoo local (`docker-compose.local.yml`, DB `test_gbedit`):
`0 failed, 0 error(s) of 1 tests`.

## Notas de entorno

- La imagen local de Odoo traía PyPDF2 1.x; `isep_openeducat_reports` necesita
  la API nueva (`PdfReader`) y el módulo enterprise `sign` la vieja
  (`PdfFileReader`). Para los tests locales se fijó `PyPDF2==2.12.1` (soporta
  ambas) dentro del contenedor `odoo16irg_local`. Conviene añadirlo a la imagen
  (`docker/odoo-local`) para que persista tras recrear el contenedor.
