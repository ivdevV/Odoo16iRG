# Registro de Ejecución - Misión: Certificados MNC (Neuropsicología Clínica) 1 Página y Bordes

## Diagnóstico y Análisis
- **Plantillas DOCX de origen**: `Plantilla-certificado-notas-raimon.docx` y `Plantilla-certificado-notas-dpto.docx`.
- **Causa raíz del desborde a 2 páginas**:
  - Los másteres de Neuropsicología Clínica (MNC) contienen 23 asignaturas (`EN01..EN11` + `RN01..RN12`).
  - La plantilla DOCX por defecto venía maquetada con márgenes normales (72pt), espaciado entre párrafos por defecto, altura de fila 315 dxa y fuente 11pt con salto automático.
  - Párrafos vacíos redundantes en el cuerpo añadían espacio vertical vertical excesivo.
- **Causa raíz del borde grueso anormal tras la fila #12**:
  - La plantilla tiene 12 filas de asignaturas por defecto. La fila #12 tenía explícitamente `<w:bottom w:val="single" w:color="000000" w:sz="10"/>`.
  - Al clonar filas adicionales para las asignaturas 13..23, la fila #12 conservaba el borde inferior negro grueso `000000`, creando una línea de separación extraña entre `EN11` y `RN01`.

## Acciones de Implementación
1. **Modificación de `irg_gradebook_certificates`**:
   - Archivo: `addons-extra/extrairg/irg_gradebook_certificates/models/irg_certificate_request.py`
   - Si `len(subjects) > 15`:
     - Márgenes superior e inferior de sección fijados a 45 pt.
     - Eliminación de párrafos vacíos en el cuerpo (sin imágenes).
     - Espaciado de párrafo fijado en `space_before=1pt`, `space_after=1pt`, `line_spacing=1.0`.
     - Altura de filas de tabla en `200` dxa con regla `atLeast`.
     - Tamaño de fuente de celdas a `6.5 pt`.
   - Iteración de normalización de bordes en `all_data_rows`:
     - Filas `0..N-2`: borde inferior `dee2e6`, sz=5.
     - Fila `N-1`: borde inferior `000000`, sz=10.

2. **Modificación de `irg_certificate_partial`**:
   - Archivo: `addons-extra/extrairg/irg_certificate_partial/models/irg_certificate_request.py`
   - Aplicada la misma maquetación dinámica y normalización de bordes cuando `len(subject_notes) > 15`.

3. **Pruebas Unitarias**:
   - Añadida prueba `test_19_mnc_23_subjects_fits_one_page_and_fixes_borders` en `irg_gradebook_certificates`.
   - Añadida prueba `test_09_partial_mnc_23_subjects_fits_one_page_and_fixes_borders` en `irg_certificate_partial`.

## Verificación
- **Ejecución en Odoo Local**:
  - Generación de PDF convertidos con LibreOffice y leídos con PyMuPDF (`fitz`).
  - Resultado: **1 página exactamente** para ambos firmantes (`raimon` y `dpto`).
  - Inspección XML de celdas: Fila #12 (`EN11`) tiene borde `dee2e6` y Fila #23 (`RN12`) tiene borde `000000`.
