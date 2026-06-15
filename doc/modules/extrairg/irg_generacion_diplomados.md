# irg_generacion_diplomados

**Categoría:** extrairg
**Versión:** 16.0.1.0.4
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** Instituto Raimon Gaja
**Depende de:** `openeducat_core`, `web`, `website`

---

## ¿Qué hace este módulo?

Permite la generación y registro histórico de diplomados independientes iRG en formato QWeb-PDF de dos páginas. 

- **Página 1 (Anverso):** Muestra el título del diplomado, el nombre del estudiante, las fechas de celebración, la duración (en horas y créditos ECTS) y la fecha de impresión.
- **Página 2 (Reverso):** Contiene el desglose de las asignaturas a cursar divididas en dos secciones independientes: Módulos Presenciales y Módulos Online.

Las asignaturas que figurarán en el diplomado se configuran como texto libre (campos de texto plano independientes) a nivel de curso y son editables directamente ("al vuelo") en el asistente antes de realizar la impresión.

---

## Funcionalidades principales

- **Configuración por curso:** Extensión de `op.course` con campos de texto plano (`irg_diplomado_subjects_presencial` e `irg_diplomado_subjects_online`) para preconfigurar los bloques de asignaturas que componen el diplomado de forma libre.
- **Acceso controlado:** Extensión de `op.student` con el botón de acción "Generar Diplomado" y un campo computado `can_generate_diplomado` que habilita el botón únicamente cuando el alumno tiene al menos un curso finalizado (`state == 'finished'`).
- **Historial histórico:** Modelo `irg.diplomado.registry` que guarda un registro permanente de cada diplomado emitido (incluyendo los textos exactos de las asignaturas en los campos `subjects_presencial` y `subjects_online`) con su correspondiente número de folio/secuencia único, permitiendo su reimpresión exacta en cualquier momento.
- **Asistente interactivo (Wizard):** El wizard `irg.diplomado.wizard` asiste al usuario cargando dinámicamente los datos sugeridos del lote/curso del estudiante y permitiendo editar las fechas, horas, créditos y modificar de forma textual los bloques de asignaturas presenciales y online antes de emitir el documento.

---

## Modelos

| Modelo | Tipo | Descripción / Campos principales |
|--------|------|----------------------------------|
| `op.course` | Extensión | Añade `irg_diplomado_subjects_presencial` y `irg_diplomado_subjects_online` (campos de texto plano). |
| `op.student` | Extensión | Añade botón inteligente y campo computado `can_generate_diplomado`. |
| `irg.diplomado.registry` | Nuevo | Almacena el registro histórico (Nombre, curso, fechas, folio único `name`, tipo de diploma, y campos de texto plano `subjects_presencial` y `subjects_online` con el contenido exacto emitido). |
| `irg.diplomado.wizard` | Nuevo | TransientModel para parametrizar la generación, con campos editables `subjects_presencial` y `subjects_online` cargados por defecto del curso. |

---

## Estructura de Vistas y UI

- `views/op_course_views.xml` — Añade la pestaña "Asignaturas Diplomado" con campos de texto para configurar los bloques por defecto.
- `views/op_student_views.xml` — Añade el botón inteligente "Diplomados" (acceso directo al histórico de ese estudiante), el botón de cabecera "Generar Diplomado" y el botón para desarrolladores "Generar Diplomado (Debug)".
- `views/diplomado_registry_views.xml` — Lista, formulario de solo lectura, búsqueda del histórico de diplomas y menú de acceso en *Educación / Registro de Diplomados*.
- `wizard/diplomado_wizard_views.xml` — Formulario emergente para la configuración de la impresión, mostrando áreas de texto editable para las asignaturas.

---

## Seguridad y Datos de Secuencia

- `security/ir.model.access.csv` — Otorga accesos de lectura/escritura y creación a los modelos del módulo para los usuarios del sistema.
- `data/ir_sequence_data.xml` — Secuencia numérica `irg.diplomado.registry.seq` para la generación del número de folio único con formato `DIP-{YYYY}-{MM}-{5_digitos}` (ejemplo: `DIP-2026-06-00001`).

---

## Reportes QWeb-PDF

- **Estructura base:** Definida en `reports/diplomado_report.xml` que establece un formato de página (`report.paperformat`) A4 horizontal (Landscape) sin márgenes (`margin_top = 0`, `margin_bottom = 0`, `margin_left = 0`, `margin_right = 0`).
- **Maquetación Full Bleed (Hoja completa sin márgenes):** Implementada en `reports/diplomado_templates.xml` (desde la versión 16.0.1.0.4) para permitir un fondo de sangrado completo en la impresión y visualización exacta del PDF. 
  - Se omiten las plantillas de diseño estándar de Odoo (como `web.basic_layout` o `div.article`) y se utiliza únicamente `web.html_container` en la raíz para evitar que el framework añada elementos HTML/CSS y márgenes predeterminados que rompan el flujo.
  - Se remueven márgenes predeterminados de Odoo mediante CSS y directivas globales `@page { size: A4 landscape; margin: 0 !important; }` sobre los divs contenedores de la plantilla (`html, body, body.container, #wrapwrap, main, .article, .page`).
  - Se elimina el uso de la clase `.page` de Odoo en los contenedores del anverso y reverso para evitar paddings impuestos por Bootstrap.
  - La escala se fija estrictamente en `1.0` (sin multiplicadores como `1.08`) para mantener una relación de aspecto 1:1.
  - Para tolerar errores de redondeo de píxeles/milímetros en el motor `wkhtmltopdf` y evitar saltos de página erróneos, las dimensiones del lienzo se configuran a `297mm x 200mm` (dejando `10mm` de tolerancia vertical frente a los `210mm` del formato A4 físico).
  - Los elementos del pie de página (como las firmas y sus imágenes) se posicionan con seguridad a una altura máxima de `184mm` vertical (`top: 184mm;`).
- **Plantilla QWeb:** Genera una estructura de dos páginas:
  - **Página 1 (Anverso):** Logotipos, firmas y datos principales posicionados con precisión sobre el fondo de sangrado completo.
  - **Página 2 (Reverso):** Cabecera y listado secuencial de los bloques de asignaturas cargados de los campos textuales `subjects_presencial` y `subjects_online`.

---

## Instalación / Actualización

```bash
# Instalación inicial
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_generacion_diplomados --stop-after-init

# Actualización/Upgrade de cambios
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_generacion_diplomados --stop-after-init
```

---

## Pruebas Unitarias Automatizadas

Las pruebas están ubicadas en `tests/test_diplomado_generation.py` y cubren los siguientes casos:
1. **`test_01_can_generate_diplomado_computation`:** Verifica que un alumno solo pueda generar diplomados cuando finalice su inscripción de curso (`state == 'finished'`).
2. **`test_02_wizard_defaults_and_onchange`:** Verifica que los métodos onchange carguen de forma correcta los valores sugeridos del estudiante, lote, curso y textos por defecto de las asignaturas en el wizard.
3. **`test_03_registry_generation_and_report_action`:** Simula el envío del wizard confirmando la generación del diploma, validando que se cree el registro histórico correspondiente en la base de datos con sus textos de asignaturas asociados y que devuelva la acción del reporte QWeb.

Para ejecutar los tests locales:
```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_generacion_diplomados --test-enable --test-tags=irg_generacion_diplomados --stop-after-init --log-level=info
```

---

## Historial de Cambios

### Versión 16.0.1.0.4
- **Reemplazo de Many2many por campos de Texto Plano**:
  - Remoción completa del uso de `op.subject` y sus relaciones Many2many en `op.course` (añadiendo `irg_diplomado_subjects_presencial` e `irg_diplomado_subjects_online`), en el wizard `irg.diplomado.wizard` (campos `subjects_presencial` y `subjects_online`) y en el registro histórico `irg.diplomado.registry` (campos `subjects_presencial` y `subjects_online`).
  - Posibilidad de definir y editar directamente el plan de estudios del diplomado como texto libre sin restricciones de modelos relacionados.
- **Resolución de problemas de maquetación Full Bleed sin Márgenes**:
  - Configuración del formato de página A4 Landscape a 0 márgenes en `report.paperformat`.
  - Reemplazo del layout `web.basic_layout` por una estructura directa con `web.html_container` para evitar la doble anidación HTML generada por Odoo.
  - Remoción de la clase `.page` de las páginas del reporte y sobrescritura de estilos CSS de contenedores para anular la limitación de ancho de Bootstrap.
  - Configuración de escala a `1.0` y reducción de altura útil de página a `200mm` (tolerancia de 10mm) con reubicación vertical de firmas a `184mm` para evitar la generación de una tercera página en blanco por desbordamiento con `wkhtmltopdf`.

### Versión 16.0.1.0.3
- **Adición del botón de depuración**:
  - Incorporación del botón **"Generar Diplomado (Debug)"** en la cabecera de la ficha del estudiante.
  - Restricción del botón al grupo `base.group_no_one` (Modo Desarrollador), permitiendo a administradores y técnicos generar/probar el formato de maquetación de diplomas con cualquier alumno sin requerir que su curso esté finalizado al 100%.

### Versión 16.0.1.0.1
- **Corrección de ParseError en instalación limpia**:
  - Remoción de la relación Many2many `course_ids` en `op.subject` y de su filtrado directo en la vista XML del wizard (`domain`).
  - Reemplazo por un filtrado dinámico en Python mediante la respuesta de los métodos `@api.onchange` en `_onchange_student_id` y `_onchange_course_id`, permitiendo la correcta instalación limpia del módulo desde cero sin colisiones de carga en la base de datos.
  - Pruebas y validaciones unitarias verificadas con éxito en Docker local.

### Versión 16.0.1.0.0
- **Estructura base completada:** Implementación limpia del módulo `irg_generacion_diplomados` en `addons-extra/extrairg/irg_generacion_diplomados`.
- **Independencia funcional:** El módulo no tiene ninguna dependencia ni herencia con el módulo antiguo `irg_generacion_diplomas`, operando de manera autónoma.
- **Ajustes de robustez en el Wizard:** Remoción de la propiedad `required=True` a nivel de campos de Python (`course_id`, `student_name`, `diplomado_name`) en el TransientModel para evitar fallos de base de datos (`NotNullViolation`) durante flujos dinámicos de pruebas o cambios en la UI, moviendo la obligatoriedad al nivel del formulario XML y a una validación explícita en el método `action_print_diplomado`.
- **Relación inversa Many2many en Subjects:** Implementación de la relación `course_ids` en `op.subject` mapeando la relación existente en Odoo para permitir filtrados correctos en el dominio del asistente en función del curso seleccionado.
- **Validación Exitosa:** Cobertura de tests unitarios del 100% completada y aprobada localmente con Docker en Odoo 16.
