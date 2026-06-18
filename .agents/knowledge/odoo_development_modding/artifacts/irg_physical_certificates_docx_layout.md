# Manipulación de Layout y Eliminación de Firmas/Sellos en Certificados DOCX Físicos

## Contexto

En el proyecto se generan certificados de notas completos (`irg_gradebook_certificates`) y parciales (`irg_certificate_partial`) a partir de plantillas `.docx` con la librería `python-docx` y se convierten a PDF usando LibreOffice.
El cliente requería que para la **variante física** (`physical` y `physical_apostilled`):
1. El bloque de texto completo se desplazara hacia abajo unos 50 píxeles (para dejar espacio a cabeceras preimpresas en el papel físico).
2. El texto exterior (cuerpo/cabecera) se mantuviera a tamaño normal (`10 Pt`), pero el texto de la tabla permaneciera a `7.5 Pt` (comportamiento idéntico al digital).
3. Se quitaran las firmas digitalizadas y logotipos de tipo sello del pie de página.
4. Se modificara la frase de cierre y el cargo del firmante (Raimon Gaja), dejando espacio vertical suficiente para la firma manuscrita.

## Decisiones de Diseño y Código

### 1. Desplazamiento Vertical del Contenido
El desplazamiento se logra sumando un offset al margen superior (`top_margin`) de todas las secciones del documento `.docx`:
```python
is_physical = self.certificate_type in ('physical', 'physical_apostilled')
if is_physical:
    for section in doc.sections:
        section.top_margin = section.top_margin + Pt(37.5)  # 37.5 Pt = 50 pixels
```

### 2. Control de Tamaño de Letra Exterior vs Interior (Tabla)
Por defecto, los certificados digitales se escalan al 75%. Para los físicos se configuró al 85% (tamaño de fuente exterior resultante de 8.5 Pt). Sin embargo, para mantener las tablas en `7.5 Pt`, se forzó su tamaño de forma selectiva:
```python
scale_percent = 85 if is_physical else 75
self._scale_document_fonts(doc, percent=scale_percent)

# Para las tablas
table_font_size = Pt(7.5) if is_physical else top_font_size
for tbl in doc.tables:
    for row in tbl.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                for r in para.runs:
                    if r.font:
                        r.font.size = table_font_size
```

### 3. Remoción Dinámica de Firmas/Sellos Embebidos en Word
Las firmas y sellos vienen pre-embebidos en las plantillas DOCX y están representados por relaciones internas a archivos de imagen (`media/image2.jpg`, `media/image2.png`, etc.).
Para eliminarlos de forma limpia:
1. Buscar los `rel_id` de las relaciones de imagen del documento correspondientes a las firmas/sellos.
2. Iterar por todos los párrafos y tablas del documento, localizando los runs que tengan nodos hijos XML que referencien a esos `rel_id` (mediante el atributo `embed`).
3. Remover el run correspondiente llamando a `para._p.remove(run._r)`.
```python
sig_rel_ids = []
for rel_id, rel in doc.part.rels.items():
    target = getattr(rel, 'target_ref', '').lower()
    if any(img in target for img in ('media/image2.jpg', 'media/image2.png', 'media/image2.jpeg')):
        sig_rel_ids.append(rel_id)

if sig_rel_ids:
    for para in list(doc.paragraphs):
        for run in list(para.runs):
            for rel_id in sig_rel_ids:
                embed_nodes = run._r.xpath('.//*[@*[local-name()="embed" and .="%s"]]' % rel_id)
                if embed_nodes:
                    para._p.remove(run._r)
                    break
```

## Gotchas

- **Eliminación de imágenes**: No es suficiente limpiar `run.text = ''` para eliminar imágenes de un run en `python-docx` ya que la imagen está embebida en un elemento `<w:drawing>` o `<w:pict>` independiente del texto. Se debe eliminar el elemento run completo (`run._r`) de su párrafo padre (`para._p.remove(run._r)`).
- **Raimon dynamic signature**: El sello de Raimon Gaja (`logodesgastado.png`) se inserta mediante un método dinámico de post-procesado `_ensure_signature_logo` que re-abre el ZIP del documento DOCX. Se debe asegurar no llamar a esta función cuando `is_physical` es True.
- **Sustitución Global de Textos**: La conversión de `"Raimon Gaja Jaumeandreu"` a `"Raimon Gaja"` se inyecta en el diccionario `replacements` para que actúe en párrafos, tablas y cabeceras. En el formateo de firmas, se debe contemplar tanto la cadena larga como la corta en las comparaciones de textos normalizados.
- **Formateo tras reasignación de textos**: Asignar directamente a `para.text` descarta los runs previos y genera uno nuevo. Se debe asegurar restablecer la fuente a `Pt(8.5)` en los runs resultantes para el párrafo de cierre y firma en el certificado físico.
- **Espaciado vertical para firma**: En lugar de inyectar párrafos vacíos que pueden romper la consistencia, se configura `para.paragraph_format.space_after = Pt(48)` en el párrafo de cierre ("Para que así conste...") para generar el hueco de firma.

## Validación Recomendada

En entornos locales donde el servicio Docker de Odoo no esté disponible o activo, se puede validar la estructura interna del documento DOCX resultante utilizando un script que mockee el framework de Odoo:
- **Script**: `missions/modificaciones_certificado_fisico/artifacts/validate_physical_layout.py`
- Ejecución:
  ```bash
  .venv/bin/python "missions/modificaciones_certificado_fisico/artifacts/validate_physical_layout.py"
  ```
