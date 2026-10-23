# Nombre de descarga de un PDF de slide

## Gotcha

En el botón «Descargar» de eLearning el nombre no lo pone `Content-Disposition`. Lo pone el atributo `download` (documentos) o `filename` de html2pdf (artículos). FileSaver copia esa cadena a `a.download` y no añade `.pdf`.

Si el título contiene un punto, el navegador usa lo que va después del último punto como extensión. «Ferrer et al. (2021)» o «13.Fluencia» se guardan sin `.pdf`. «….pptx» se guarda como PowerPoint aunque el binario sea `application/pdf`.

## Patrón

`ensurePdfName` en `website_slides_customizations/static/src/frontend/download.js`:

- Sanea `\ / : * ? " < > |` y recorta. Vacío → `documento`.
- Si ya acaba en `.pdf`, se deja, incluidas las mayúsculas.
- Si no, se concatena `.pdf`. No se recorta una extensión de ofimática: `nombre.pptx` pasa a `nombre.pptx.pdf`.

Hay que aplicarla en los dos sitios. El bundle de este módulo no reescribe la extensión.

## Otro handler

`irg_website_slides_download_fix` registra un clic en captura sobre `#custom_download_button` y llama a su propio `downloadPDF` con el título crudo. Si ese módulo está instalado, el arreglo de `download.js` no llega a ejecutarse.
