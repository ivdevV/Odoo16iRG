# irg_content_interactive_super_fix

## 1. Titulo corto
Fix de `_super` en contenido interactivo fullscreen.

## 2. Resumen objetivo
Corregir el error `this._super is not a function` al abrir contenidos/examenes en eLearning cuando esta instalado `isep_content_interactive`. El cambio conserva el render nativo de documentos y solo sustituye el asset defectuoso.

## 3. Motivo / justificacion
En produccion falla un bundle frontend que incluye `isep_content_interactive/static/src/js/slides_course_player_fullscreen.js`. Ese archivo ejecuta `await this._fetchHtmlContent()` y despues llama a `this._super(...arguments)`, pero en las clases legacy de Odoo `_super` no esta garantizado despues de una pausa asincrona. Beta funciona sin este modulo/fallo, por lo que el objetivo es alinear produccion eliminando el asset defectuoso, no reimplementar todo el reproductor fullscreen.

## 4. Alcance exacto
- Asset frontend en `web.assets_frontend`.
- Reemplazo del archivo `isep_content_interactive/static/src/js/slides_course_player_fullscreen.js` mediante la directiva `replace` de assets de Odoo 16.
- No se modifican modelos, vistas, controladores ni modulos existentes.

## 5. Diseno tecnico
- Modulo tecnico: `irg_content_interactive_super_fix`.
- `depends`: `isep_content_interactive`.
- El JS reemplazado mantiene la funcionalidad original de contenido embebido, pero captura `const renderSuper = this._super.bind(this)` al inicio de `_renderSlide`, antes de cualquier `await`.
- Cuando el slide no usa HTML embebido, se llama a `renderSuper(...arguments)` para preservar documentos, infografias, quizzes y demas renderizado nativo/custom previo.

## 6. Dependencias
`isep_content_interactive`.

## 7. Backwards-compatibility / migracion
No anade datos persistentes ni modifica esquema. Si `isep_content_interactive` no esta instalado, este modulo no debe instalarse. Si esta instalado, solo cambia el asset cargado en frontend.

## 8. Casos de prueba / criterios de aceptacion
- Abrir en produccion un examen/slide fullscreen sin `this._super is not a function`.
- Abrir documentos en pantalla completa manteniendo el iframe/contenedor nativo de Odoo.
- Abrir contenido interactivo embebido manteniendo auto-altura, scroll y descarga desde iframe.
- Confirmar que beta y produccion difieren por la presencia/version de `isep_content_interactive` o por el bundle de assets.

## 9. Rollback plan
Desinstalar `irg_content_interactive_super_fix` o revertir el commit y actualizar assets:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> -u isep_content_interactive --stop-after-init --db_host=pgodoo_latest
```

## 10. Estimacion y responsable
Estimacion: 45 minutos. Responsable: iRG / GitHub Copilot.