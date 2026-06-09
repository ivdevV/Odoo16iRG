# irg_generacion_diplomas

**Categoría:** extrairg
**Versión:** 16.0.1.0.10
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** ISEP / iRG
**Depende de:** `openeducat_core`, `web`, `website`

---

## ¿Qué hace este módulo?

Permite generar diplomas físicos y digitales para los alumnos directamente desde la ficha del estudiante. Soporta nombres de cursos en catalán, genera automáticamente un código QR y un número de registro para cada diploma, y tiene diseño adaptado para nombres de cursos largos.

Dependencias externas Python: `qrcode`, `reportlab`.

## Funcionalidades principales

- Wizard de generación de diplomas desde `op.student`.
- Soporte para diplomas físicos y digitales.
- Gestión de nombres de cursos en catalán.
- Generación automática de QR y número de registro.
- Plantilla de diseño adaptada para cursos con nombres largos.
- Página de verificación de diploma en el sitio web.
- Secuencia numérica para los diplomas.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.diploma.wizard` (nuevo) | Nuevo | Alumno, tipo, curso en catalán |

## Vistas y UI

- `views/op_course_views.xml` — campo de nombre en catalán en el formulario de curso.
- `wizard/diploma_wizard_views.xml` — wizard de generación.
- `views/op_student_views.xml` — botón de diploma en la ficha del alumno.
- `views/diploma_verify_templates.xml` — página de verificación web.

## Notas técnicas

- Dependencias externas: `pip install qrcode reportlab` en el contenedor.
- Requiere `security/ir.model.access.csv`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_generacion_diplomas \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_generacion_diplomas \
    --stop-after-init --db_host=pgodoo_latest
```

## Historial de Cambios

### Versión 16.0.1.0.10 (V3.2)
- **Corrección efectiva del hueco superior en diplomas físicos**:
  - Se desplazan los anclajes superiores de título e introducción hacia el centro mediante `upper_gap_reduction`, reduciendo el espacio real entre las dos columnas superiores.
  - El ajuste se limita a diplomas físicos y no modifica el bloque inferior, orientación, firmas, QR ni tamaño de página.

### Validación 16.0.1.0.10

```bash
python3 -m py_compile addons-extra/extrairg/irg_generacion_diplomas/reports/diploma_pdf_report.py
git diff --check -- addons-extra/extrairg/irg_generacion_diplomas/reports/diploma_pdf_report.py addons-extra/extrairg/irg_generacion_diplomas/__manifest__.py doc/modules/extrairg/irg_generacion_diplomas.md
```

Resultado: correcto.

### Versión 16.0.1.0.9 (V3.1)
- **Ajuste de separación superior en diplomas físicos**:
  - El bloque superior de títulos e introducciones usa ahora el ancho completo de columna en diplomas físicos, igualando el espacio central con el bloque inferior de texto.
  - En el título catalán físico, el salto antes de la conjunción `i` se fuerza explícitamente para que `i de la Salut` quede en segunda línea, equivalente a la composición castellana `y de la Salud`.
  - La preposición central `a` se eleva ligeramente solo en diplomas físicos para aumentar la separación respecto al nombre del alumno.
  - No se modifica orientación, tamaño de página, columnas inferiores, firmas, QR ni estilos tipográficos.

### Validación 16.0.1.0.9

```bash
python3 -m py_compile addons-extra/extrairg/irg_generacion_diplomas/reports/diploma_pdf_report.py
```

Resultado: correcto.

La validación Odoo local con `docker-compose.local.yml` no pudo ejecutarse porque Docker no estaba disponible en la máquina (`docker.sock` inaccesible).

### Versión 16.0.1.0.8 (V3.0)
- **Incremento de Tamaños de Fuente y Espaciado en Diplomas Físicos**:
  - **Fuentes de Cabecera**: Se incrementó el tamaño de la fuente para las líneas introductorias/cabecera a `sf(10.5)` (anteriormente `sf(9.5)`).
  - **Fuentes de Cuerpo**: Se incrementó el tamaño de la fuente para el cuerpo de texto legal a `sf(9.5)` (anteriormente `sf(8.5)`).
  - **Espaciado de Línea (body_line_gap)**: Se incrementó el gap entre líneas del cuerpo de texto legal a `sp(14)` (anteriormente `sp(13)`).
  - Estos ajustes se aplican condicionalmente en `diploma_pdf_report.py` para diplomas de tipo físico (`diploma_type == 'physical'`), mejorando la legibilidad e impacto visual.

### Versión 16.0.1.0.7 (V2.9)
- **Alineación de Columnas de Título contra el Gutter Central en Diplomas Físicos**:
  - **Alineación contra el Gutter**: En diplomas físicos (`diploma_type == 'physical'`), se modificó el posicionamiento horizontal del título y la cabecera (intro) para alinearlos contra el canal central (gutter). La columna izquierda se sitúa en `(left_col_x + col_width) - left_title_width` (alineada a la derecha de su espacio) y la columna derecha en `right_col_x` (alineada a la izquierda de su espacio).
  - **Prevención de Ensanchamiento del Gap**: Esto impide que el centrado individual de los bloques de texto ensanche el gap central, asegurando que la separación central entre columnas se mantenga óptima y no se vea afectada por el tamaño de los títulos.

### Versión 16.0.1.0.6 (V2.8)
- **Refinamiento de Fuentes, Espaciados y Ancho de Títulos en Diploma Físico**:
  - **Remoción de Negrita**: Se quitó la negrita de los nombres de los firmantes y del número de registro en diplomas físicos, usando la tipografía regular (`font_regular`) para una presentación estética más limpia y elegante.
  - **Reducción de Gap Vertical**: Se redujo a `sp(10)` el espaciado vertical entre el nombre y el rol/cargo de los firmantes (`role_y = sign_text_y - sp(10)`) en diplomas físicos.
  - **Limitación de Ancho de Título**: Se limitó el ancho máximo de los títulos en diplomas físicos a `col_width * 0.82` (`left_title_width` / `right_title_width = col_width * 0.82`) para forzar de manera controlada el salto de línea en expresiones específicas como "de la Salut / de la Salud".

### Versión 16.0.1.0.5 (V2.7)
- **Ajustes de Alineación Horizontal y Ancho de Columnas en Diploma Físico**:
  - **Unificación de Ancho de Columnas**: Se unificó el ancho de columna del título y las líneas introductorias con el del cuerpo inferior para diplomas físicos, logrando una alineación simétrica y consistente.
  - **Desactivación de la Compresión para Textos Cortos**: Se desactivó el mecanismo de compresión o reducción de ancho (`left_title_width` / `right_title_width`) para títulos y cabeceras de longitud corta, impidiendo deformaciones tipográficas y mejorando la legibilidad.

### Versión 16.0.1.0.4 (V2.6)
- **Ajustes de Alineación y Reducción de Fuentes en Diploma Físico**:
  - **Alineación Perfecta de Columnas**: Alineación de la coordenada Y inicial del cuerpo de texto legal en catalán y castellano mediante `y_start_body`, igualando `y_es = y_start_body` y unificando el retorno mediante `y = min(y, y_es)` para evitar desfasajes en columnas asimétricas.
  - **Reducción de Fuentes en Formato Físico**: Disminución del tamaño de la fuente para cabeceras (intro) a `sf(9.5)` (vs `sf(11)`), cuerpo de texto legal a `sf(8.5)` (vs `sf(10)`) con un gap entre líneas reducido a `sp(13)` (vs `sp(15)`), y fechas a `sf(9.5)` (vs `sf(11)`) para prevenir solapamientos e incrementar la holgura visual del diploma impreso.

### Versión 16.0.1.0.3 (V2.5)
- **Ajustes de Maquetación para Diplomas Físicos**:
  - **Reducción de Gutter Horizontal**: Reducción del margen y separación horizontal lateral (gutter) para optimizar el espacio impreso en diplomas físicos.
  - **Menor Separación entre Párrafos**: Reducción del espaciado vertical entre párrafos de texto para compactar el cuerpo del documento.
  - **Subida del Bloque de Firmas y QR**: Elevación del bloque inferior (firmas y código QR) decrementando la coordenada vertical condicionalmente.

### Versión 16.0.1.0.2 (V2.4)
- **Ajustes de Maquetación y Alineación**:
  - **Bajada del Título**: Aumento del margen superior del título a `y -= sp(48)` para centrar y equilibrar verticalmente el bloque de texto superior.
  - **Compactado de Elementos Centrales**: Ajuste y reducción del espaciado para la preposición "a" (`sp(14)`) y el nombre del estudiante (`sp(22)`) para dar mayor aire al resto de elementos y mejorar la cohesión del diploma.
  - **Alineación del Registro y Código QR**: Enlace vertical del código QR y su texto de registro ("Nº Registro: ...") con la línea de roles (`role_y`), garantizando una alineación horizontal uniforme tanto para diplomas digitales como físicos.

### Versión 16.0.1.0.1 (V2.3)
- **Mejora Estética del Layout**: Se ajustó la posición de renderizado vertical de los nombres de los másteres en el PDF de ReportLab. Se modificó el desplazamiento vertical de `y -= sp(28)` a `y -= sp(38)` en la línea 215 del generador. Esto añade un espaciado visual (aire) de 10 puntos respecto a la cabecera superior. Las posiciones de los elementos subsiguientes se calculan dinámicamente de forma relativa a este desplazamiento, manteniendo la cohesión y previniendo solapamientos en todo el diploma.
