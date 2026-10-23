# Plan — Nombre de descarga PDF en slides de eLearning

## Clasificación

- Misión: `full`. Es un bugfix que cambia el comportamiento del botón «Descargar» (el archivo que guarda el navegador).
- Tier: `standard`. La lógica es local, el contexto está cerrado por el diagnóstico del 23/10/2026 y el código de producción tocado es un solo asset JS. No hay arquitectura cruzada, concurrencia, migración ni borrado de datos.
- Capacidad: razonamiento sólido de implementación y pruebas. El runtime de esta sesión no permite elegir otro modelo; se usa el modelo de la sesión.

## Conocimiento consultado

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_elearning_url_slide.md` (superficie eLearning; no aplica el gotcha `nbr_<categoria>`)
- `.agents/workflows/odoo16_codebase_knowledge.md`
- `.agents/skills/odoo16_developer/SKILL.md` y `.agents/INSTRUCTIONS.md`
- Diagnóstico `DIAGNOSTICO_descarga_bin.md` y el listado de 377 slides (no se modifican datos)

La skill pide no editar módulos existentes. El encargo restringe el arreglo a `website_slides_customizations/static/src/frontend/download.js`. Prevalece el encargo: se edita ese asset y nada más del producto.

## Problema

`download_as_pdf` pasa el título de la slide, sin extensión, a `link.download` y a `html2pdf` (`opt.filename`). El navegador trata el texto posterior al último punto como extensión. Un título como «Ferrer et al. (2021)…», «Act. en clase» o «13.Fluencia» se guarda sin `.pdf`. Un título que acaba en `.pptx` se guarda con esa extensión falsa. El binario y el `Content-Type` (`application/pdf`) ya son correctos. Hay 377 documentos afectados en PROD; no se tocan.

`html2pdf.js` (jsPDF / FileSaver) asigna `a.download` al `filename` tal cual. No añade `.pdf` por su cuenta. La misma función tiene que cubrir documentos y artículos.

## Decisión: extensión de ofimática

Si el nombre ya termina en `.pdf` (sin distinguir mayúsculas), se deja igual.

Si termina en otra extensión (`.pptx`, `.docx`, `.ppt`, `.doc`, `.xlsx` o cualquiera que no sea `.pdf`), se **añade** `.pdf` al final. «Parte 2-nov2024.pptx» queda «Parte 2-nov2024.pptx.pdf».

No se sustituye la cola. Motivos:

1. El título es el nombre visible de la slide. En datos reales esa cola forma parte del título (slide 2087 acaba en «.pptx»). Sustituirla borra texto del título.
2. Una lista cerrada de extensiones de ofimática queda siempre corta (`.odp`, `.key`, `.csv`, `.txt`…). La regla única «si no acaba en `.pdf`, añadir `.pdf`» cubre el punto intermedio y la extensión falsa.
3. El navegador usa el tramo posterior al último punto. «….pptx.pdf» tiene extensión `pdf`.
4. Coincide con la función propuesta en el diagnóstico y evita un `.pdf.pdf` cuando el título ya acaba en `.pdf`.

## Alcance

Incluido:

- `ensurePdfName(name)` en `addons-extra/addons_uisep/website_slides_customizations/static/src/frontend/download.js`.
- Usarla en `downloadPDF(url.href, ensurePdfName(name))` y en `filename` de las opciones de `html2pdf`.
- Test Node aislado de esa función (QUnit/hoot de Odoo 16 no es viable: no hay Docker ni `docker-compose.local.yml` en este entorno).
- Artefactos de misión, changelog y una nota de conocimiento reutilizable.

`ensurePdfName`:

1. `null`, `undefined` o no-texto se coerciona a texto. El vacío (también solo espacios, o vacío tras sanear) pasa a `documento`.
2. Sustituye cada racha de `\ / : * ? " < > |` por un espacio y recorta extremos.
3. Si el resultado acaba en `.pdf` (insensible a mayúsculas), lo devuelve sin cambiar las mayúsculas.
4. Si no, concatena `.pdf`.

Fuera de alcance:

- Rutas, controladores, permisos, vistas XML, `ir.attachment` y cualquier renombrado de slides.
- Despliegue, limpieza de caché de assets en beta/PROD y apertura de PR.
- Versión del manifest. Sigue en `0.1`. `AGENTS.md` no exige subirla. El formato `16.0.x.x.x` de las instrucciones de módulos nuevos no autoriza a reescribir el esquema de un módulo legado dentro de este arreglo mínimo. Odoo invalida el bundle de assets por el checksum del fichero.
- `addons-extra/extrairg/irg_website_slides_download_fix`. Si ese módulo está instalado, su listener en fase captura llama a su propio `downloadPDF` / `html2pdf` con el título crudo y puede dejar este arreglo sin efecto. El encargo limita el cambio al JS de `website_slides_customizations`. Queda como riesgo residual, no como segundo cambio.

## Criterios de aceptación

- Título con punto intermedio → el nombre acaba en `.pdf` y conserva el punto interno.
- Título sin punto → título + `.pdf`.
- Título acabado en `.pptx` (y el resto de ofimática citada) → se conserva la cola y se añade `.pdf`.
- Título acabado en `.PDF` → se conserva tal cual, sin duplicar la extensión.
- Título vacío, solo espacios o vacío tras quitar caracteres prohibidos → `documento.pdf`.
- Caracteres `\ / : * ? " < > |` no aparecen en el resultado.
- No cambian rutas, controladores, permisos ni datos.

## Riesgos

- El módulo `irg_website_slides_download_fix` puede interceptar el clic. Hay que comprobar en el entorno de despliegue si está instalado antes de dar el bug por cerrado en PROD.
- Hace falta regenerar assets al desplegar. Este encargo no despliega.
- El saneado es solo el nombre local de la descarga. No sustituye controles de acceso del servidor. `/slides/slide/<slug>/pdf_content` sigue igual.
- Nombres muy largos pueden chocar con el límite del sistema de archivos. No se trunca: el título debe seguir siendo reconocible.

## Seguridad

No hay autenticación, concurrencia, migración, secretos, configuración de despliegue ni borrado histórico. El nombre solo alimenta el atributo `download` y la opción `filename` de `html2pdf`. Aun así, `.agents/INSTRUCTIONS.md` pide veredicto del Security Advisor antes de documentar. Se pide antes de implementar. Un `[NO]` bloquea el código.

## Pruebas

1. RED: test Node que carga `download.js` y exige `ensurePdfName` con los casos de arriba. Tiene que fallar antes del cambio.
2. GREEN: la función mínima y los dos call sites. El test pasa.
3. `node --check` del JS de producción y del test.
4. Diff acotado al archivo previsto más test y documentación.
5. E2E TestSprite (`e2e_testsprite`): **sí se dispara**. El diff toca `static/`. Se ejecuta después del resto de checks y solo si ninguno ha fallado. `projectPath` sería el directorio del módulo, contra runtime local en el puerto 8069 y una base desechable. En esta sesión no hay Docker ni `docker-compose.local.yml`. Si sigue así en la validación, el check queda `skipped` con esa causa y el estado de la misión no puede ser `passed`.

## Roles

| Fase | Rol |
| --- | --- |
| Plan | Orquestador de esta sesión |
| Seguridad previa | Security Advisor (subagente distinto) |
| Implementación / TDD | Codificador de esta sesión |
| Review | Subagente revisor, sin editar código de producción |
| Validación | Subagente validador, sin editar código de producción |
| E2E | e2e-tester, solo si el runtime local existe y el resto está en verde |
| Documentación | Esta sesión, después de Review y Validación |
| Publicación | Push solo a `cursor/slides-pdf-download-name-e49d`. Sin PR, sin push a `Dev_iRG`, sin merge, sin despliegue |
