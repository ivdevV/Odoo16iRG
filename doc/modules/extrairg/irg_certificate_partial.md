# Referencia Técnica: irg_certificate_partial

Este documento provee la especificación técnica completa y de referencia para el módulo `irg_certificate_partial`.

---

## Ficha Técnica

| Propiedad | Valor |
| --- | --- |
| **Nombre Técnico** | `irg_certificate_partial` |
| **Categoría** | Academic / Website |
| **Versión** | `16.0.1.0.0` |
| **Licencia** | LGPL-3 |
| **Instalable** | Sí |
| **Aplicación** | No |
| **Autor** | iRG |

### Dependencias

El módulo interactúa y depende de los siguientes componentes del sistema:
- `irg_gradebook_certificates` (Módulo base de gestión de solicitudes de certificados)
- `irg_campus_certificates_portal` (Interfaz unificada de certificados en el portal)

---

## Descripción General

El módulo `irg_certificate_partial` implementa la lógica específica para la generación de los **Certificados de Notas Parciales** (`gradebook_partial`). A diferencia del certificado completo (que exige cerrar la libreta con estado `done`), el certificado parcial se puede solicitar y generar mientras el alumno está cursando el programa académico (`state == 'in_progress'`).

### Características principales:
- **Estado Académico Flexible:** Se puede emitir con libretas activas.
- **Formateo de Notas Pendientes:** Si una asignatura obligatoria no tiene exámenes calificados (o su cantidad de calificaciones registradas es inferior al número de exámenes mínimos configurados en la libreta), se muestra el texto `"Pendiente"` en lugar de la nota numérica `0.0`.
- **Cálculo de la Nota Media:** La Nota Media final reflejada en el certificado se calcula de forma dinámica, promediando única y exclusivamente aquellas asignaturas que dispongan de calificaciones completas (los valores float) y excluyendo los registros marcados como `"Pendiente"`. Si todas las asignaturas obligatorias están pendientes, la Nota Media final se reporta como `"Pendiente"`.
- **Ajustes de Diseño en Plantilla Word:**
  - **Adición de Dos Puntos en "CERTIFICA":** Se busca dinámicamente el bloque de texto exacto `"CERTIFICA"` en los párrafos de la plantilla Word y se reemplaza por `"CERTIFICA:"` para alinearse a las directrices formales.
  - **División y Alineación a la Izquierda:** El texto explicativo largo se divide en tres oraciones/párrafos independientes. Todos se fuerzan a una alineación izquierda (`0` o `LEFT` en la estructura OpenXML) para evitar que el renderizado de Word estire artificialmente las palabras (justificación forzada).
  - **Espaciado de Párrafos (`Pt(12)`):** Se define un margen inferior (`space_after`) de `Pt(12)` en cada uno de los tres nuevos párrafos explicativos para garantizar un espaciado vertical armónico.
  - **Réplica de Márgenes y Sangrías:** Para asegurar que los párrafos adicionales mantengan la coherencia con el diseño del documento, se copian las propiedades de formato de márgenes e indentación del párrafo original: `left_indent`, `right_indent`, `first_line_indent`, `space_before` y `line_spacing`.

---

## Diseño Técnico

### 1. Modelos (`models/irg_certificate_request.py`)

Hereda el modelo base `irg.certificate.request` para modularizar la lógica de rellenado:

* **Carga de Plantilla (`_get_template_path`):**
  - Si el tipo de documento es `gradebook_partial`, localiza y utiliza de forma compartida las plantillas oficiales de notas del módulo `irg_gradebook_certificates` (`Plantilla-certificado-notas-dpto.docx` o `Plantilla-certificado-notas-raimon.docx` según el firmante) mediante `get_module_resource`. Esto previene duplicar archivos y simplifica el mantenimiento.

* **Reemplazo Dinámico (`_fill_template`):**
  - Sobrescribe la lógica de llenado del documento Word.
  - Itera sobre las asignaturas de tipo obligatorio (`compulsory`).
  - Obtiene el número total de exámenes requeridos (`qty` de tipo `exam` definido en las líneas de la plantilla de libreta).
  - Compara contra los resultados registrados del estudiante:
    - Si la lista de resultados de tipo `exam` está vacía o el número de resultados es inferior al requerido, la nota se establece como `"Pendiente"`.
    - De lo contrario, se formatea la nota real a dos decimales y se añade al grupo para promediar.
  - Modifica el párrafo de descripción de la plantilla, dividiéndolo en tres párrafos de texto independientes e inyectados uno tras otro, estableciendo explícitamente su alineación como `LEFT` (izquierda) en la estructura OpenXML para garantizar un diseño limpio sin justificaciones estiradas.
  - Genera dinámicamente la tabla XML del documento docx reemplazando los textos de código, nombre y nota.
  - Sobrescribe la celda del pie de tabla ("Nota Media") para mostrar el promedio dinámico calculado o `"Pendiente"` si corresponde.
  - Corrige el texto del párrafo `"CERTIFICA"` agregándole los dos puntos (`"CERTIFICA:"`).
  - Duplica el formato original del párrafo principal (indentaciones izquierda/derecha, primera línea, espaciado interlineal, etc.) en los párrafos inyectados para el Máster y ECTS, y añade un espaciado inferior (`space_after`) de `Pt(12)` en cada párrafo.

### 2. Formato de la primera frase descriptiva

En el certificado parcial (`document_type == 'gradebook_partial'`), la primera frase descriptiva del `.docx` se reconstruye mediante runs segmentados para aplicar negrita únicamente a los datos nominales principales:

- Nombre del alumno: `partner.name`.
- Nombre del curso o máster: `course_name`.

El resto de la frase conserva el estilo normal de la plantilla. La segmentación se realiza con el helper `_replace_paragraph_text_with_bold_segments()`, que reemplaza el contenido del párrafo por runs nuevos y preserva las propiedades del primer run original cuando existen. Esta lógica evita aplicar negrita al párrafo completo y mantiene el formato base de la plantilla Word.

---

## Suite de Pruebas Automatizadas

El módulo incluye un set de pruebas en `tests/test_partial.py`:
- `test_01_partial_gradebook_fill_template`: Crea un estudiante con dos asignaturas obligatorias. Una completa (2/2 exámenes calificados) y otra incompleta (1/2 exámenes). Valida que se genere el certificado parcial, que la asignatura completa tenga su nota numérica, la incompleta aparezca como `"Pendiente"`, y la nota media final sea igual a la nota de la asignatura completa.
- `test_02_partial_gradebook_first_sentence_has_bold_student_and_course`: Genera el certificado parcial y abre el `.docx` resultante para validar que la primera frase contiene el alumno y el curso esperados, y que ambos aparecen en runs independientes con `bold == True`.
- `test_03_partial_gradebook_all_pending_fill_template`: Comprueba el comportamiento del módulo en casos límites donde todas las asignaturas obligatorias están pendientes. Valida que el certificado se cree correctamente y que la nota media final se imprima como `"Pendiente"`.

### Validación documentada del cambio de negritas

Validación realizada sobre el cambio de formato de la primera frase:

```bash
python3 -m py_compile addons-extra/extrairg/irg_certificate_partial/models/irg_certificate_request.py addons-extra/extrairg/irg_certificate_partial/tests/test_partial.py
git diff --check -- addons-extra/extrairg/irg_certificate_partial/models/irg_certificate_request.py addons-extra/extrairg/irg_certificate_partial/tests/test_partial.py
```

Ambos comandos finalizaron correctamente.

Limitación conocida: no se ejecutó el test Odoo local porque el daemon de Docker no estaba activo en el entorno de validación. La comprobación de contenedores devolvió:

```text
Cannot connect to the Docker daemon at unix:///Users/ivrogo/.docker/run/docker.sock. Is the docker daemon running?
```

---

## Instalación y Pruebas Locales

```bash
# Instalar y ejecutar tests
docker exec -it odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_certificate_partial --test-enable --stop-after-init
```

---

## Historial de Cambios (Changelog)

### [16.0.1.0.0] - 2026-06-05
- **Corrección de formato:** En el certificado parcial de notas, la primera frase descriptiva del `.docx` ahora aplica negrita solo al nombre del alumno y al nombre del curso/máster mediante runs segmentados.
- **Calidad:** Añadido test automatizado para verificar que alumno y curso/máster se generan en runs con `bold == True`; validación local limitada por Docker daemon inactivo.

### [16.0.1.0.0] - 2026-06-03
- **Mejora:** Implementación inicial de la lógica de Certificados de Notas Parciales.
- **Corrección de Diseño:**
  - Sustitución de `"CERTIFICA"` por `"CERTIFICA:"`.
  - División de la descripción de matrícula en tres párrafos con alineación `LEFT` y espaciado de párrafo configurado en `Pt(12)`.
  - Configuración del copiado de propiedades de formato (`left_indent`, `right_indent`, `first_line_indent`, `space_before`, `line_spacing`) en los párrafos resultantes para evitar desajustes visuales.
- **Funcionalidad:**
  - Tratamiento dinámico de asignaturas con calificaciones pendientes (visualización de `"Pendiente"` en lugar de `0.0`).
  - Cálculo dinámico de la Nota Media ignorando asignaturas pendientes.
- **Calidad:** Cobertura de tests unitarios para escenarios de calificaciones parciales y totalmente pendientes.
