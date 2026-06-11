# irg_gradebook_certificates

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP / iRG
**Depende de:** `isep_gradebook`, `website_sale`, `sale`, `portal`, `mail`, `website`

---

## ¿Qué hace este módulo?

Gestiona la solicitud y generación de certificados de notas para alumnos. Hay dos flujos:
- **Backend (admin/docente):** wizard directo que genera e imprime el PDF al instante.
- **Portal (alumno):** solicitud online con pago previo a través de la tienda.

Tipos de certificado disponibles: Digital (30€), Físico (40€), A Medida (40€), Físico Apostillado (80€). Se añaden cargos de envío Nacional (+20€) o Internacional (+60€) para los físicos.

## Funcionalidades principales

- Modelo de solicitud de certificado con estado y flujo de aprobación.
- Generación de PDF QWeb del certificado de notas.
- Wizard de generación desde el backend.
- Decoración global de arcos azules en la esquina inferior derecha de los certificados Word/PDF generados.
- Formato alineado del certificado final de notas, equivalente al certificado parcial: bloque descriptivo inicial en tres párrafos, alumno y curso en negrita, bloques estáticos alineados a la retícula de tabla, `CERTIFICA:`, cierre justificado, firma en dos líneas y texto legal vertical compacto.
- Tienda online para pedido de certificados por el alumno (con pago).
- Cron para procesar solicitudes pendientes.
- Plantillas de email para notificaciones de estado.
- Secuencia numérica para los certificados.
- Reglas de seguridad por alumno.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.certificate.request` (nuevo) | Nuevo | Alumno, tipo, estado, pago, PDF |

## Vistas y UI

- `views/irg_certificate_request_views.xml` — gestión en el backend.
- `views/app_gradebook_student_views.xml` — botón de solicitud en la libreta del alumno.
- `views/menu.xml` — acceso desde menú.

## Notas técnicas

- Requiere `security/ir.model.access.csv` y `security/record_rules.xml`.
- Usa `data/sequence_data.xml`, `data/product_data.xml`, `data/mail_templates.xml`, `data/cron_data.xml`.
- El helper `_ensure_bottom_right_arcs()` inserta `static/src/img/RCOS.png` en el `.docx` generado como `word/media/bottom_right_arcs.png`, con anclaje de página `right/bottom` y `behindDoc="1"`, para que no desplace texto, cierre ni firma. Se aplica a certificados completos, asistencia, matrícula y es reutilizado por el certificado parcial.
- El helper `_remove_header_logo(docx_path)` elimina las imágenes o gráficos de la cabecera del documento Word. Descomprime el archivo `.docx` (formato ZIP), analiza `word/header1.xml`, localiza los elementos XML `<w:r>` que contienen dibujos, imágenes o gráficos flotantes (`<w:drawing>`, `<w:AlternateContent>`, o `<w:pict>`), los elimina del árbol XML, y regenera el ZIP.
- Para los certificados físicos (físico y físico apostillado), se excluye el logo de la cabecera aplicando `_remove_header_logo()` y se omiten los arcos decorativos inferiores (no se ejecuta `_ensure_bottom_right_arcs()`), con el fin de no interferir con el diseño del papel timbrado preimpreso.
- El helper `_ensure_signature_logo(docx_path)` inyecta el logo digitalizado desgastado `logodesgastado.png` (de `static/src/img/`) junto a la firma de Raimon Gaja en certificados donde el firmante es `raimon`. Busca el párrafo que contiene "Raimon Gaja" e "Instituto Raimon", comprueba que no se encuentre ya insertado el logo, y agrega un run con la imagen redimensionada a un ancho de 120 pt.
- La unificación de tamaño de letra de la tabla busca el tamaño de fuente del primer párrafo con texto en la cabecera superior del documento (`top_font_size`). Si se localiza, se recorren recursivamente todas las celdas de las tablas del documento `.docx` y se ajusta el tamaño de la fuente (`r.font.size`) de todos sus runs al valor de `top_font_size`, asegurando uniformidad visual.
- El certificado final de notas (`document_type == 'gradebook'`) aplica `_format_gradebook_static_paragraphs()`, `_compact_gradebook_vertical_legal_text()` y `_restore_gradebook_vertical_legal_text()` para mantener la estructura visual equivalente al certificado parcial. La firma `Departamento Académico Instituto Raimon Gaja` se convierte en dos líneas, el cierre se justifica con el ancho de la tabla, y el texto legal vertical se fuerza a 5 pt (`w:val="10"`) para evitar saltos de línea. Además, la plantilla base `Plantilla-certificado-notas-dpto.docx` fue remaquetada para cambiar el anclaje de la imagen de la firma de flotante (`wp:anchor`) a en línea con el texto (`wp:inline`) dentro de un párrafo vacío independiente para prevenir colisiones de maquetación.
- El helper `_replace_gradebook_description_paragraph()` reconstruye el primer bloque descriptivo del certificado final para que sea un calco del certificado parcial: primera frase con nombre del alumno y curso en negrita, segunda frase de ECTS detallados, y tercera frase `Las calificaciones obtenidas son:`. Los tres párrafos usan la misma retícula de anchura que la tabla y espaciado inferior de 12 pt.
- El método `_replace_in_paragraph(paragraph, old, new)` realiza una sustitución segura de placeholders en párrafos cuyos runs han sido divididos por Word. Para evitar la pérdida de firmas digitalizadas u otros elementos multimedia representados como elementos gráficos (`<w:drawing>`), el método ahora recorre y limpia exclusivamente las etiquetas de texto `<w:t>` dentro de los runs secundarios, en lugar de vaciar el run completo. Además, se actualizó la aserción en los tests de certificados parciales para validar que el dibujo se encuentre inline en el párrafo independiente.

## Changelog

- **2026-06-11:**
  - Implementada la exclusión de logos de cabecera y arcos decorativos en los certificados físicos. Se añadió el helper `_remove_header_logo()` para eliminar las imágenes de la cabecera (`word/header1.xml`) y se condicionó la aplicación de los arcos azules inferiores (`_ensure_bottom_right_arcs()`) para que solo se ejecute en certificados no físicos.
  - Implementada la unificación del tamaño de letra de la tabla de notas con el del cuerpo superior (`top_font_size`).
  - Añadido el helper `_ensure_signature_logo()` que inyecta la firma desgastada digitalizada de Raimon Gaja (`logodesgastado.png`) al lado del bloque de firma textual.
- **2026-06-10:** El certificado final de notas replica el bloque textual inicial del certificado parcial para ambos firmantes (`raimon` y `dpto_academico`): tres párrafos independientes, alumno/curso en negrita y anchura/espaciado equivalente al parcial.

## Validación

```bash
python3 -m py_compile addons-extra/extrairg/irg_gradebook_certificates/models/irg_certificate_request.py addons-extra/extrairg/irg_gradebook_certificates/tests/test_certificate_request.py addons-extra/extrairg/irg_certificate_partial/models/irg_certificate_request.py addons-extra/extrairg/irg_certificate_partial/tests/test_partial.py
git diff --check -- addons-extra/extrairg/irg_gradebook_certificates/models/irg_certificate_request.py addons-extra/extrairg/irg_gradebook_certificates/tests/test_certificate_request.py addons-extra/extrairg/irg_certificate_partial/models/irg_certificate_request.py addons-extra/extrairg/irg_certificate_partial/tests/test_partial.py doc/modules/extrairg/irg_gradebook_certificates.md doc/modules/extrairg/irg_certificate_partial.md
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_gradebook_final_partial_layout_20260605 --test-enable --stop-after-init -i irg_gradebook_certificates,irg_certificate_partial --test-tags /irg_gradebook_certificates,/irg_certificate_partial --http-port=8099 --log-level=test
```

Resultado esperado:

```text
odoo.tests.result: 0 failed, 0 error(s) of 15 tests when loading database 'test_irg_gradebook_final_partial_layout_20260605'
```

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_gradebook_certificates \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_gradebook_certificates \
    --stop-after-init --db_host=pgodoo_latest
```
