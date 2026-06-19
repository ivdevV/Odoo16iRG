# Changelog - Módulo `irg_diploma_graduacion_student`

**Fecha:** 2026-06-19  
**Autor:** Documentador Subagent  
**Descripción del cambio:** Incorporación de la funcionalidad para generar diplomas de graduación en formato PDF a partir de una plantilla Word (`.docx`) y conversión mediante LibreOffice, accesible mediante un asistente (wizard) desde la ficha del estudiante en OpenEduCat (`op.student`).

---

## Cambios Introducidos

### Funcionalidades y Negocio
- **Generación de Diploma en PDF**: Se implementa un flujo que permite al personal de administración de la institución generar el diploma de graduación oficial en formato PDF para cualquier estudiante registrado. La maquetación se realiza procesando dinámicamente un documento Word de plantilla y transformándolo a PDF sin intervención manual.
- **Asistente de Configuración (Wizard)**: Antes de generar el diploma, se presenta un wizard que permite:
  - Seleccionar/Verificar el estudiante (precargado automáticamente).
  - Seleccionar el curso académico concreto del estudiante (filtrado mediante dominio dinámico para que solo aparezcan sus matrículas activas/históricas).
  - Elegir la fecha de expedición del diploma (por defecto, el día actual).

### Componentes Técnicos Añadidos

#### 1. Modelos Heredados (`models/op_student.py`)
- **`op.student`**: Se añade el método `action_open_graduation_diploma_wizard` para abrir el asistente con el contexto del estudiante actual preseleccionado.

#### 2. Modelos Nuevos (Wizard) (`wizard/diploma_graduacion_wizard.py`)
- **`irg.diploma.graduacion.wizard`** (`TransientModel`):
  - Campos: `student_id` (Many2one a `op.student`, obligatorio), `student_course_id` (Many2one a `op.student.course`, obligatorio, filtrado por estudiante), y `date` (Date, fecha de expedición).
  - Método `_normalize_catalan_course_name`: Normalización de caracteres acentuados y palabras comunes en catalán (por ejemplo, reemplazar "Máster" por "Màster", "y" por "i").
  - Método estático `_replace_in_paragraph`: Limpieza y reemplazo seguro de marcadores dinámicos (`<<...>>`) a nivel de `run` de python-docx para evitar fragmentación del texto que rompa las variables de sustitución.
  - Método `action_print_pdf`: 
    - Renderización de las fechas formateadas con localización (mediante Babel, fallback a strftime local si falla).
    - Mapeo de variables dinámicas:
      - `<<Alumno>>` y `<<alumno>>` -> Nombre del estudiante.
      - `<<Master>>` y `<<curso>>` -> Nombre del curso en castellano.
      - `<<MasterCat>>` -> Nombre del curso en catalán (con normalización).
      - `<<Fecha>>` -> Fecha en castellano ("19 de junio de 2026").
      - `<<FechaCat>>` -> Fecha en catalán ("19 de juny de 2026").
    - Procesamiento de la plantilla Word (`plantilla_diploma_graduado.docx`) en párrafos, tablas, cabeceras y pies de página.
    - Conversión a PDF mediante LibreOffice Headless en entorno Docker (`libreoffice --headless ...`).
    - Almacenamiento del PDF en Odoo como un adjunto asociado al modelo `op.student`.
    - Retorno de una acción de descarga directa URL (`ir.actions.act_url`).

#### 3. Vistas y Menús (`views/` y `wizard/`)
- `views/op_student_views.xml`: Inyección mediante XPath de un botón `Diploma Graduación` con estilo resaltado (`oe_highlight`) en la cabecera (`<header>`) de la ficha de estudiante (`op.student`).
- `wizard/diploma_graduacion_wizard_views.xml`: Vista formulario del asistente (`irg.diploma.graduacion.wizard`) con controles para los campos configurados, y botones `Generar PDF` (acción primaria) y `Cancelar`.

#### 4. Seguridad (`security/ir.model.access.csv`)
- Se define el acceso completo (`read`, `write`, `create`, `unlink`) para el modelo `irg.diploma.graduacion.wizard` asignado a todos los usuarios del grupo interno base (`base.group_user`).

#### 5. Plantilla de Maquetación (`static/src/templates/plantilla_diploma_graduado.docx`)
- Plantilla oficial de diploma de graduado con los marcadores de sustitución.

---

## Pruebas Realizadas y Resultados

### Pruebas Unitarias e Integración (`tests/test_diploma.py`)
Se implementó la suite de pruebas unitarias bajo `TransactionCase`:
1. **`setUp`**: Creación de un estudiante (`op.student`), una pareja de socio/partner (`res.partner`), un curso académico (`op.course` con soporte para nombre catalán si existe), una promoción/lote (`op.batch`) y la matrícula del estudiante (`op.student.course`).
2. **`test_graduation_diploma_wizard_flow`**:
   - Ejecución del botón del formulario (`action_open_graduation_diploma_wizard`) y validación de que retorna la estructura correcta de ventana de asistente.
   - Creación del wizard en memoria con los registros creados.
   - Ejecución del método `action_print_pdf`.
   - Validación de que la acción de descarga retornada es de tipo `ir.actions.act_url` y contiene la URL de descarga del adjunto.
   - Búsqueda en base de datos del archivo adjunto generado (`ir.attachment`), comprobando que se vincula correctamente al registro de estudiante (`op.student`), que el tipo MIME sea `application/pdf` y que contenga datos binarios no vacíos.

### Resultados de Ejecución de Pruebas
- **Comando ejecutado localmente:**
  ```bash
  odoo-bin -c /etc/odoo/odoo.conf -i irg_diploma_graduacion_student --test-tags /irg_diploma_graduacion_student
  ```
- **Resultado:**
  - `checks`: unit_tests -> pass
  - `details`: 1 test passed, 0 failed, 0 errors.
  - La traza completa se encuentra en `missions/irg_diploma_graduacion_student/artifacts/test-output.log`.
