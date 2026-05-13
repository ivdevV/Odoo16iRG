# Micro-spec: `irg_tfm_acta_documento` — Generación de Actas de TFM/TFG

**Fecha:** 2026-05-13  
**Módulo:** `irg_tfm_acta_documento`  
**Versión:** 16.0.1.0.0  
**Owner:** Equipo IRG  

---

## 1. Resumen y objetivo

Crear un módulo que genere actas de evaluación (PDF) para Trabajos Finales de Máster (TFM) y Grado (TFG). El acta es un documento oficial que contiene:

**Campos inamovibles (prellenados por secretaría):**
- Titulación
- Curso académico
- Alumno (Nombre, Apellidos, DNI)
- Título del trabajo
- Director/a TFT
- Tribunal (Presidente, Secretario/a)

**Campos editables (rellenables por tribunal en PDF):**
- Fecha de defensa
- Calificación
- Observaciones
- Firma del Secretario

---

## 2. Motivo / Contexto del cambio

Santiago (Dirección iRG) solicita una solución para:
1. Generar actas de TFM/TFG como PDF editable (no sellado).
2. Reducir trabajo manual: la mayoría de datos vienen de secretaría y son inamovibles.
3. Mantener coherencia visual con la identidad iRG (logos, colores, tipografía).
4. Permitir rellenar tres espacios críticos: Calificación, Observaciones y Firma.

---

## 3. Alcance exacto

### Incluido
- Modelo `irg.tfm.acta` para registrar actas de TFM/TFG.
- Wizard `irg.tfm.acta.wizard` para generar PDF desde el estudiante.
- Generación PDF con ReportLab (siguiendo patrón de `irg_generacion_diplomas`).
- Dos modelos de acta: TFM y TFG.
- Campos de datos inamovibles y editables como se describe en sección 1.
- Guardado de acta en `ir.attachment` para auditoría.
- Vista de estudiante con botón de generar acta.

### Excluido
- Formularios web interactivos para rellenar acta (solo PDF).
- Verificación de QR (a diferencia de diplomas, actas no llevan QR).
- Integración con firma digital (se deja abierto para futuro).
- Gestión de versiones/borradores.

---

## 4. Diseño técnico

### 4.1 Modelos

#### `irg.tfm.acta` (Nuevo)
```python
{
  'name': 'Nombre acta (formato: ALUMNO - TFM/TFG - AAAA)',
  'student_id': Many2one(op.student),
  'student_course_id': Many2one(op.student.course),
  'academic_year': Char,  # ej. "2025-2026"
  'degree_name': Char,  # ej. "Máster Universitario en ..."
  'student_name': Char,
  'student_surnames': Char,
  'student_dni': Char,
  'tfm_title': Text,
  'director_name': Char,
  'director_surnames': Char,
  'president_name': Char,
  'president_surnames': Char,
  'secretary_name': Char,
  'secretary_surnames': Char,
  'acta_type': Selection([('tfm', 'TFM'), ('tfg', 'TFG')]),
  'defense_date': Date,
  'grade': Char,  # ej. "8.5 / 10"
  'observations': Text,
  'attachment_id': Many2one(ir.attachment),
  'state': Selection([('draft', 'Borrador'), ('valid', 'Válida')]),
  'created_date': Datetime,
}
```

#### `irg.tfm.acta.wizard` (Transient)
```python
{
  'student_id': Many2one(op.student),
  'student_course_id': Many2one(op.student.course),
  'acta_type': Selection([('tfm', 'TFM'), ('tfg', 'TFG')]),
  'degree_name': Char,  # selector o textarea
  'academic_year': Char,
  'tfm_title': Text,
  'director_name': Char,
  'director_surnames': Char,
  'president_name': Char,
  'president_surnames': Char,
  'secretary_name': Char,
  'secretary_surnames': Char,
  'defense_date': Date,
}
```

### 4.2 ReportLab PDF Generator

Crear `reports/acta_pdf_report.py` similar a `irg_generacion_diplomas`:

- Método `generate_acta_pdf(data, acta_type)` que devuelve bytes.
- Estructura de 2 páginas:
  - **Página 1:** Datos fijos del alumno, tribunal, título.
  - **Página 2:** Secretario/a, fecha defensa, calificación, observaciones, firma (espacios en blanco para rellenar).
- Logos de iRG en encabezado.
- Tipografía Inter (fallback Helvetica).
- Escalabilidad para A4.

### 4.3 Vistas XML

#### Vista del wizard (`wizard/acta_wizard_views.xml`)
- Formulario con campos: acta_type, degree_name, academic_year, tfm_title, director, presidente, secretario.
- Botón "Generar PDF".

#### Vista del estudiante (`views/op_student_views.xml`)
- Herencia en la vista del estudiante.
- Botón "Generar Acta TFM/TFG" que abre el wizard.

#### Vista de registro de actas (`views/acta_views.xml`)
- Lista y formulario de actas creadas.
- Campos: student, degree_name, defense_date, grade, observations, state.

### 4.4 Security

- `security/ir.model.access.csv`: ACLs para `irg.tfm.acta` (read para usuarios portal, create/write/delete para staff).

### 4.5 Assets

- `static/src/img/`: logos iRG (reutilizar si existen en `irg_generacion_diplomas`).
- `static/src/fonts/`: fonts Inter (reutilizar).

---

## 5. Dependencias

```python
{
  'depends': [
    'base',
    'web',
    'website',
    'openeducat_core',  # para op.student y op.student.course
    'irg_generacion_diplomas',  # para reutilizar logos, fonts, y patrón ReportLab
  ],
  'external_dependencies': {
    'python': ['reportlab', 'qrcode', 'babel'],
  },
}
```

---

## 6. Compatibilidad / Migración

- **Nueva instalación:** no hay datos previos.
- **Upgrade:** sin cambios de esquema si es la primera versión.
- **Rollback:** desinstalación limpia (elimina attachments creados).

---

## 7. Casos de prueba

### TC-001: Crear acta TFM básica
- **Entrada:** Wizard con student_id, acta_type='tfm', datos del director y tribunal.
- **Salida:** PDF generado, acta registrada en estado 'valid'.
- **Validación:** Archivo descargable, contiene campos inamovibles correctos.

### TC-002: Crear acta TFG
- **Entrada:** acta_type='tfg'.
- **Salida:** PDF generado con modificaciones visuales para TFG si aplican.
- **Validación:** Diferenciable de TFM.

### TC-003: PDF editable
- **Entrada:** Acta generada, abrir en lector PDF.
- **Salida:** Espacios en blanco para Calificación, Observaciones, Firma (sin limitaciones técnicas).
- **Validación:** Usuario puede escribir y guardar en PDF.

### TC-004: Auditoria
- **Entrada:** Generar acta.
- **Salida:** Registro en `irg.tfm.acta` + attachment en `ir.attachment`.
- **Validación:** Datos recuperables y trazables.

---

## 8. Rollback

Desinstalación del módulo:
1. Elimina registros de `irg.tfm.acta` (puede ser cascade u otro patrón).
2. Elimina attachments asociados.
3. Limpia wizard transient.
4. Revierte herencias XML.

---

## 9. Estimación

| Tarea | Horas | Notas |
|-------|-------|-------|
| Micro-spec + diseño PDF | 1 | Incluye iteración visual. |
| Modelo + ACL + fixture | 1.5 | Reutilizar estructura de diplomas. |
| ReportLab PDF generator | 4 | Adaptar `irg_generacion_diplomas` para actas. |
| Wizard + vistas XML | 2 | Herencias simples. |
| Tests | 1.5 | TC-001, TC-002, TC-003, TC-004. |
| Documentación + changelog | 1 | Incluye guía de uso. |
| **Total** | **~11 horas** | Iteración + refinamiento incluidos. |

---

## 10. Responsable / Validación

- **Desarrollo:** Equipo IRG.
- **Validación:** Santiago Borges Rodríguez (Dirección iRG).
- **Testing:** Usuarios de secretaría + tribunal.
- **Despliegue:** Jenkins (post-merge a `Dev_iRG`).

---

## Notas finales

- Reutilizar ampliamente de `irg_generacion_diplomas` (ReportLab setup, fonts, logos, patrón wizard).
- Acta es documento **oficial** pero NO sellado (no incluye QR ni firma digital en PDF generado).
- Campos editables en PDF son **espacios en blanco** que se rellenan manualmente en Acrobat/lector PDF.
- Posible evolución futura: integrar con firma digital o formularios PDF interactivos.
