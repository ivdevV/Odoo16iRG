# irg_website_slides_render_fix

## 1. Titulo corto
Fix de renderizado fullscreen en eLearning/examenes.

## 2. Resumen objetivo
Evitar el error frontend `this._super is not a function` al abrir examenes o contenidos fullscreen de eLearning. El fix estabiliza el metodo `_renderSlide` del reproductor de `website_slides` cuando existen multiples extensiones custom asincronas.

## 3. Motivo / justificacion
El reproductor fullscreen de Odoo 16 y varios modulos custom extienden `_renderSlide` mediante `include()`. Algunas extensiones usan funciones `async` y encadenan `this._super`, un patron fragil en la clase legacy de Odoo porque `_super` solo esta garantizado durante la llamada sincronica envuelta. Se implementa un modulo extra en `addons-extra/extrairg/` para no modificar modulos nativos ni custom existentes.

## 4. Alcance exacto
- Asset frontend JS para `web.assets_frontend`.
- Override final de `_renderSlide` en el reproductor fullscreen de `website_slides`.
- Categorias cubiertas: `quiz`, mini-quiz, `certification`, `document`, `infographic`, `article`, `google_drive`, `local_external`, `bunny`, `scorm`.
- Delegacion al renderer previo para videos YouTube/Vimeo, que dependen de subwidgets privados del modulo nativo.

## 5. Diseno tecnico
- Modulo tecnico: `irg_website_slides_render_fix`.
- Herencia JS: `Fullscreen.include({ _renderSlide: ... })` sobre `@website_slides/js/slides_course_fullscreen_player`.
- No se llama a `this._super` para quizzes, certificaciones ni categorias custom afectadas.
- Se reutilizan plantillas QWeb existentes: `website.slides.fullscreen.content`, `website.slides.fullscreen.certification`, `custom_html_template`, `website.slides.fullscreen.video.google_drive`.

## 6. Dependencias
`website_slides`, `website_slides_survey`, `isep_survey`, `isep_content_interactive_survey`, `isep_external_video`, `isep_bunny_elearning`, `isep_scorm_elearning`, `isep_slide_article_custom`.

## 7. Backwards-compatibility / migracion
No anade modelos, campos ni datos persistentes. El rollback consiste en desinstalar el modulo o retirarlo de los assets y actualizar la lista de modulos.

## 8. Casos de prueba / criterios de aceptacion
- Abrir un examen/certificacion en fullscreen sin `UncaughtPromiseError`.
- Renderizar quiz y mini-quiz en fullscreen.
- Renderizar contenidos `bunny`, `scorm`, `local_external`, `document`, `infographic` y `article`.
- Verificar que los assets frontend recompilan al actualizar el modulo.

## 9. Rollback plan
```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> -u web --stop-after-init --db_host=pgodoo_latest
```
Tambien puede desinstalarse `irg_website_slides_render_fix` desde Apps si fuese necesario.

## 10. Estimacion y responsable
Estimacion: 1 hora. Responsable: iRG / GitHub Copilot.