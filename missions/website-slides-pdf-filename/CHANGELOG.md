# Changelog — website-slides-pdf-filename

## [2026-10-23] - Extensión .pdf en la descarga de slides

### Corregido

- El botón «Descargar» de `website_slides_customizations` ya no usa el título de la slide como nombre de archivo.
- `ensurePdfName` quita `\ / : * ? " < > |`, usa `documento` si el nombre queda vacío y añade `.pdf` cuando el título no termina ya en `.pdf`.
- Un título acabado en `.pptx`, `.docx`, `.ppt`, `.doc` o `.xlsx` conserva esa cola y queda en `….pptx.pdf`. Así el archivo que guarda el navegador termina en `.pdf`.
- Afecta a la descarga de documentos (`downloadPDF`) y a la de artículos (`html2pdf`). No cambia el PDF guardado en Odoo ni las 377 slides afectadas.

### Pruebas

- Test Node aislado: `node --test addons-extra/addons_uisep/website_slides_customizations/static/tests/ensure_pdf_name.test.js`.
- QUnit de Odoo 16 no se ejecutó: en esta sesión no hay Docker ni `docker-compose.local.yml`.

### Limitaciones

- La versión del manifest sigue en `0.1`. `AGENTS.md` no pide subirla.
- Si `irg_website_slides_download_fix` está instalado, su listener puede seguir descargando con el título crudo. Este cambio no lo toca.
- La E2E con TestSprite no se ejecutó: no había runtime local en el puerto 8069. No está validada en navegador.
- Al desplegar hará falta que Odoo regenere el bundle `web.assets_frontend`. Este encargo no despliega.
