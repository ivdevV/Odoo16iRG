# Website slides customizations

El botón «Descargar» de la lección vive en `static/src/frontend/download.js`.

## Nombre del archivo

`ensurePdfName` construye el nombre con el que el navegador guarda el PDF:

- Sustituye `\ / : * ? " < > |` por un espacio.
- Si el título queda vacío, el nombre es `documento`.
- Si no termina en `.pdf` (sin distinguir mayúsculas), añade `.pdf`.
- Una cola `.pptx`, `.docx` u otra distinta de `.pdf` se conserva: `titulo.pptx.pdf`.

Sirve para documentos (`/pdf_content`) y para artículos generados con `html2pdf`. No cambia la ruta, el controlador ni el binario.

El navegador trata como extensión el texto que va después del último punto. Sin este sufijo, un título como «Ferrer et al. (2021)» se guarda sin `.pdf`.

## Prueba

```bash
node --test addons-extra/addons_uisep/website_slides_customizations/static/tests/ensure_pdf_name.test.js
```

El test no entra en `web.assets_frontend`: el manifest lista los assets uno a uno.

## Limitaciones

`irg_website_slides_download_fix`, si está instalado, intercepta el clic y usa su propia copia del título. En ese caso este archivo no decide el nombre.

La versión del módulo sigue en `0.1`.
