# irg_generacion_diplomados

**Categoría:** extrairg  
**Versión:** 16.0.1.0.4  
**Licencia:** LGPL-3  
**Instalable:** Sí  
**Autor:** Instituto Raimon Gaja  
**Depende de:** `openeducat_core`, `web`, `website`  

---

## ¿Qué hace este módulo?

Permite la generación y registro histórico de diplomados independientes iRG en formato PDF de dos páginas generadas programáticamente en el servidor utilizando **ReportLab**.

- **Página 1 (Anverso):** Muestra el título del diplomado, el nombre del estudiante, las fechas de celebración, la duración (en horas y créditos ECTS) y la fecha de impresión. En la variante digital se dibuja un fondo de sangrado completo, el logotipo institucional superior `logo_irg.png`, las firmas de la dirección ampliadas e idóneamente distribuidas, y un código QR dinámico en la esquina inferior izquierda para la verificación del folio del registro.
- **Página 2 (Reverso):** Contiene el desglose de las asignaturas a cursar divididas en dos secciones independientes: Módulos Presenciales y Módulos Online. Las asignaturas se distribuyen de forma equilibrada en dos columnas por bloque con una tipografía aumentada para asegurar su perfecta legibilidad.

Las asignaturas que figurarán en el diplomado se configuran como texto libre (campos de texto plano independientes con salto de línea) a nivel de curso y son editables directamente ("al vuelo") en el asistente antes de realizar la impresión. Se eliminaron por completo las dependencias y relaciones Many2many con `op.subject`, de modo que el plan de estudios se gestiona enteramente mediante texto plano para mayor flexibilidad operativa.

---

## Funcionalidades principales

- **Configuración por curso:** Extensión de `op.course` con campos de texto plano (`irg_diplomado_subjects_presencial` e `irg_diplomado_subjects_online`) para preconfigurar los bloques de asignaturas del diplomado de forma libre, permitiendo escribir saltos de línea para listar las materias.
- **Acceso controlado:** Extensión de `op.student` con el botón de acción "Generar Diplomado" y un campo computado `can_generate_diplomado` que habilita el botón únicamente cuando el alumno tiene al menos un curso finalizado (`state == 'finished'`).
- **Historial histórico:** Modelo `irg.diplomado.registry` que guarda un registro permanente de cada diplomado emitido, incluyendo los textos exactos de las asignaturas en los campos `subjects_presencial` y `subjects_online` (campos de texto plano). También guarda su correspondiente número de folio/secuencia único, permitiendo su descarga directa o reimpresión inmutable mediante el archivo adjunto generado (`ir.attachment`).
- **Asistente interactivo (Wizard):** El wizard `irg.diplomado.wizard` asiste al usuario cargando dinámicamente los datos sugeridos del lote/curso del estudiante y permitiendo editar las fechas, horas, créditos y modificar de forma textual (mediante campos de texto libre `subjects_presencial` y `subjects_online`) las asignaturas presenciales y online antes de emitir el documento.
- **Arquitectura de Impresión ReportLab (Full Bleed):** Generación robusta del PDF en memoria en el servidor, persistencia del documento en `ir.attachment` y redirección inmediata a descarga directa vía URL, evitando dependencias del motor local de wkhtmltopdf y asegurando un diseño a hoja completa sin márgenes de página.

---

## Modelos

| Modelo | Tipo | Descripción / Campos principales |
|--------|------|----------------------------------|
| `op.course` | Extensión | Añade `irg_diplomado_subjects_presencial` y `irg_diplomado_subjects_online` (campos de texto plano) para almacenar el listado predeterminado de asignaturas. |
| `op.student` | Extensión | Añade botón inteligente y campo computado `can_generate_diplomado` para restringir el acceso a la generación. |
| `irg.diplomado.registry` | Nuevo | Almacena el registro histórico permanente del diploma emitido (Nombre, curso, fechas, folio único `name`, tipo de diploma, relación `attachment_id` con el PDF generado, y campos de texto plano `subjects_presencial` y `subjects_online` que congelan el contenido del plan de estudios). |
| `irg.diplomado.wizard` | Nuevo | TransientModel para parametrizar la generación, con campos editables `subjects_presencial` y `subjects_online` (texto plano) cargados por defecto del curso. Retorna la acción de descarga directa del PDF generado. |

---

## Estructura de Vistas y UI

- `views/op_course_views.xml` — Añade la pestaña "Asignaturas Diplomado" con campos de texto multilínea para configurar los bloques por defecto.
- `views/op_student_views.xml` — Añade el botón inteligente "Diplomados" (acceso directo al histórico de ese estudiante), el botón de cabecera "Generar Diplomado" y el botón para desarrolladores "Generar Diplomado (Debug)".
- `views/diplomado_registry_views.xml` — Lista, formulario de solo lectura, búsqueda del histórico de diplomas y menú de acceso en *Educación / Registro de Diplomados*.
- `wizard/diplomado_wizard_views.xml` — Formulario emergente para la configuración de la impresión, mostrando áreas de texto editable para las asignaturas.

---

## Seguridad y Datos de Secuencia

- `security/ir.model.access.csv` — Otorga accesos de lectura/escritura y creación a los modelos del módulo para los usuarios del sistema.
- `data/ir_sequence_data.xml` — Secuencia numérica `irg.diplomado.registry.seq` para la generación del número de folio único con formato `DIP-{YYYY}-{MM}-{5_digitos}` (ejemplo: `DIP-2026-06-00001`).

---

## Generación de PDF con ReportLab

La maquetación y generación del diplomado se realiza a través de **ReportLab** en el archivo `reports/diplomado_pdf_report.py`. 

### Diseño y Maquetación (A4 Landscape sin márgenes):
- **Dimensiones:** Lienzo a tamaño exacto A4 horizontal (297mm de ancho por 210mm de alto) sin márgenes (`pagesize=landscape(A4)`).
- **Hoja Completa (Full Bleed):** El diseño se dibuja desde el origen `(0,0)` hasta el límite de la página `(297mm, 210mm)`. En la variante digital, el fondo del diploma (`diploma_background.jpg`) cubre toda la superficie sin bordes blancos.
- **Acceso Local a Recursos:** El fondo (`diploma_background.jpg`), el logotipo superior (`logo_irg.png`) y las firmas de la dirección (`firma_izquierda.jpg`, `firma_derecha.jpg`) se resuelven a nivel de disco local de Odoo usando `modules.get_module_resource` en lugar de peticiones HTTP externas. Esto garantiza que las firmas y logotipos nunca aparezcan como imágenes rotas.
- **Página 1 (Anverso):**
  - **Código QR:** Generado de forma dinámica a partir de la URL de verificación (por defecto la del propio Odoo o `https://institutoraimongaja.com`) mediante la librería Python `qrcode` y escrito en memoria (`io.BytesIO`). Se posiciona en la esquina inferior izquierda (`x = 22 * mm`, `y = 18 * mm`, tamaño `28 * mm x 28 * mm`).
  - **Número de Registro:** Dibujado justo debajo del código QR (`y = 12 * mm`), centrado horizontalmente, usando la fuente `Helvetica-Bold` de tamaño `8`.
  - **Logotipo Superior:** Se dibuja a un tamaño ampliado de `90 * mm` por `25 * mm`, centrado en la cabecera.
  - **Texto de Aprobación:** Utiliza la clase `Paragraph` con la hoja de estilos `ParagraphStyle` configurada con soporte para envoltura automática de texto (`wrapOn`) a un ancho máximo de `257mm` y posicionamiento con `drawOn`. Admite formato HTML básico en línea (como `<b>`).
  - **Firmas Ampliadas y Distribución Simétrica:** Para evitar solaparse con el código QR inferior izquierdo, se han ampliado y distribuido de forma equilibrada hacia el centro y la derecha del anverso:
    - *Firma Raimon Gaja (Director General):* Dibujada a un tamaño de `48 * mm` por `18 * mm`, posicionada horizontalmente a partir de la coordenada `72 * mm` y a una altura vertical de `27 * mm`.
    - *Firma Fermín Carrillo (Director de RRII):* Dibujada a un tamaño de `52 * mm` por `18 * mm`, posicionada horizontalmente a partir de la coordenada `185 * mm` y a una altura vertical de `27 * mm`.
    - *Textos de cargos:* Ubicados a las coordenadas de inicio horizontal de `56 * mm` (izq.) y `171 * mm` (der.) respectivamente, con un ancho de `80 * mm` para cada bloque de texto de firmas.
- **Página 2 (Reverso):**
  - Se genera dinámicamente llamando a `canvas.showPage()`.
  - Los bloques de "Módulos Presenciales" y "Módulos Online" leen los campos de texto plano del curso o wizard.
  - El texto libre se divide por saltos de línea y se distribuye de forma automática y equilibrada en 2 columnas (izquierda a `35mm` y derecha a `154mm`) usando envoltorios `Paragraph` de ReportLab.
  - **Aumento de Tipografía:** Para garantizar la perfecta legibilidad del listado de asignaturas del reverso:
    - *Títulos de Sección:* Fuente `Helvetica-Bold` de **`14.5pt`** con interlínea (`leading`) de `18pt`.
    - *Listado de Asignaturas:* Fuente `Helvetica` de **`13pt`** con interlínea (`leading`) de `17pt`.
  - Si un bloque no tiene asignaturas registradas, se renderiza un mensaje por defecto indicando que no se registran módulos en esa modalidad.

### Persistencia y Descarga:
1. El wizard de impresión llama a `generate_diplomado_pdf(data)`.
2. ReportLab escribe el binario en un búfer de memoria (`io.BytesIO`).
3. El wizard guarda el binario en base64 en un registro de tipo `ir.attachment` asociado al modelo `irg.diplomado.registry` y actualiza la relación `attachment_id` en el histórico.
4. El wizard retorna una acción `ir.actions.act_url` que apunta a `/web/content/<attachment_id>?download=true`, iniciando la descarga directa e inmediata en el navegador del usuario.
5. El registro histórico ofrece el botón "Reimprimir" que descarga directamente el adjunto previamente almacenado, asegurando la inmutabilidad y consistencia exacta del diplomado emitido a lo largo del tiempo.

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
3. **`test_03_registry_generation_and_report_action`:** Simula el envío del wizard confirmando la generación del diploma, validando que se cree el registro histórico correspondiente en la base de datos con sus textos de asignaturas asociados, que genere el binario en ReportLab persistiendo el adjunto `attachment_id`, y que devuelva la acción `ir.actions.act_url` para descarga directa. También verifica el método de reimpresión de un registro histórico.

Para ejecutar los tests locales:
```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_generacion_diplomados --test-enable --test-tags=irg_generacion_diplomados --stop-after-init --log-level=info
```

---

## Historial de Cambios

### Versión 16.0.1.0.4
- **Eliminación definitiva de op.subject:** Se eliminaron por completo las dependencias y relaciones Many2many con `op.subject`. Se implementaron los campos de texto plano `irg_diplomado_subjects_presencial` e `irg_diplomado_subjects_online` en el curso (`op.course`), y `subjects_presencial` y `subjects_online` en el wizard (`irg.diplomado.wizard`) y el registro histórico (`irg.diplomado.registry`).
- **Migración a ReportLab (Generación de PDF en Servidor)**:
  - Remoción completa del reporte QWeb-PDF basado en XML (`diplomado_templates.xml`) y su motor `wkhtmltopdf` debido a inestabilidades en el dibujado a sangre completa sin márgenes (Full Bleed).
  - Creación del generador `report.irg_generacion_diplomados.diplomado_pdf` basado en ReportLab para posicionamiento vectorial A4 horizontal exacto (297x210 mm) sin márgenes.
  - Carga local de assets de imagen (fondos, firmas) desde el sistema de archivos del servidor en lugar de resoluciones de red HTTP.
  - Almacenamiento persistente del PDF generado como archivo adjunto (`ir.attachment`) en el histórico del diplomado (`irg.diplomado.registry`).
  - Redirección automática de la UI para la descarga del PDF a través de la acción `ir.actions.act_url` apuntando a `/web/content/`.
- **Mejoras Visuales en el PDF (ReportLab):**
  - Adición del código QR generado dinámicamente en la esquina inferior izquierda con la URL de verificación y número de registro/folio justo debajo.
  - Actualización del logotipo superior con el nuevo asset `logo_irg.png` y aumento de sus dimensiones físicas a `90x25 mm`.
  - Ampliación física del tamaño de las firmas escaneadas (`48x18 mm` para Raimon Gaja y `52x18 mm` para Fermín Carrillo) y desplazamiento horizontal a la derecha para evitar solapamientos con el código QR y mejorar el equilibrio estético.
  - Incremento del tamaño de fuente en el reverso para mejorar sustancialmente la legibilidad del plan de estudios (`14.5pt` en títulos y `13pt` en asignaturas).

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
- **Validación Exitosa:** Cobertura de tests unitarios del 100% completada y aprobada localmente con Docker en Odoo 16.doo para permitir filtrados correctos en el dominio del asistente en función del curso seleccionado.
- **Validación Exitosa:** Cobertura de tests unitarios del 100% completada y aprobada localmente con Docker en Odoo 16.
