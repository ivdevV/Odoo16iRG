# irg_nlex_grade_exemption

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `isep_gradebook`, `isep_control_escolar`, `dec_document`, `isep_openeducat_reports`, `l10n_mx_edi_extended`

---

## ¿Qué hace este módulo?

Excluye las asignaturas cuyo código comience con la palabra `NLEX` (insensible a mayúsculas/minúsculas, por ejemplo, `NLEX01`, `nlex02`) de las libretas de calificaciones, actas digitales, certificadosSEP (DEC) e impresiones de certificados. Esto permite que no aparezcan en documentos finales y que no impidan el cierre de libretas de alumnos aunque estas no tengan calificación asignada.

## Funcionalidades principales

- **Cierre de Libreta Exento (`app.gradebook.student`):**
  - Modifica la validación en `state_to_done()` para ignorar las materias NLEX sin calificaciones o exámenes cargados.
- **Cálculo de Promedios:**
  - Excluye las calificaciones y materias NLEX del cálculo del promedio final general (`avg_score`) y promedio final acumulado (`total_final`).
  - Excluye las materias NLEX del cálculo del promedio cuatrimestral actual en el resumen de calificaciones.
- **Exportación SEP / DEC (`dec.document`):**
  - Excluye las asignaturas NLEX de los archivos de exportación de certificación electrónica de la SEP.
  - Recalcula el total de asignaturas obligatorias y el total de créditos excluyendo las materias NLEX.
- **Vistas y Reportes QWeb:**
  - Oculta las materias NLEX del reporte impreso de la libreta de calificaciones (`report_gradebook`).
  - Oculta las materias NLEX del reporte impreso del diploma o certificado de notas (`certified_diploma`).

## Vistas y Modelos Modificados

- **Modelos:**
  - `models/app_gradebook_student.py` — hereda `app.gradebook.student` para sobrescribir validaciones, promedios y exportaciones DEC.
  - `models/ap_gradebook_summary.py` — hereda `ap.gradebook.summary` para ajustar los promedios cuatrimestrales.
- **Vistas QWeb:**
  - `views/report_gradebook.xml` — hereda el reporte QWeb de la libreta para omitir filas de asignaturas NLEX.
  - `views/certified_diploma.xml` — hereda el reporte QWeb de diploma certificado para omitir materias NLEX.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_nlex_grade_exemption \
    --stop-after-init --db_host=pgodoo_local

# Actualizar
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_nlex_grade_exemption \
    --stop-after-init --db_host=pgodoo_local
```

## Pruebas Realizadas

Se han desarrollado pruebas unitarias automáticas en `tests/test_nlex_grade_exemption.py` que validan:
1. Intento de cierre de libreta fallando por falta de notas en materia regular (correcto).
2. Cierre exitoso de la libreta con materias NLEX vacías tras colocar nota en la materia regular.
3. Exclusión correcta del promedio final y promedio general de las materias NLEX.
4. Generación y validación del documento SEP (DEC) confirmando que no incluye la materia NLEX y recalcula créditos.
