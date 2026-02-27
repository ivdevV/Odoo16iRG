# Micro-spec: irg_course_portal_tiles — helpdesk + tiles adjustments

1. Título corto

irg_course_portal_tiles: añadir página helpdesk y pequeños cambios en tiles

2. Resumen objetivo (1–2 frases)

Añadir una página web de Helpdesk personalizada accesible en `/helpdesk/atencion-al-cliente-1`, ajustar el tile de "Atención" para que enlace a esa página, y añadir un subtítulo informativo para subir documentación académica. Registrar los cambios en micro-spec y mantener el módulo dentro de `addons-extra/extrairg/`.

3. Motivo / justificación

Se requiere que el portal de curso muestre un enlace consistente hacia un centro de soporte específico del alumnado y que la página muestre un titular claro para que los alumnos suban documentación solicitada por el Área Académica. Evitamos tocar core y aplicamos cambios mediante un módulo extra.

4. Alcance exacto

- Vistas: añadir `helpdesk_page.xml` en `views/` (plantilla que llama a `website_helpdesk.ticket_submit_form`).
- Controlador: añadir ruta `/helpdesk/atencion-al-cliente-1` en `controllers/main.py`.
- Templates existentes modificadas: `irg_course_portal_tiles_views.xml` (tile link apuntando al nuevo URL, texto "Cliente" → "Alumno" en render dinámico).
- Manifest: añadir `website_helpdesk` a `depends` y registrar la vista en `data`.
- Assets: archivos SCSS/JS ya añadidos en `static/src/` pero la carga por XML fue retirada; pendiente registrar via `assets` en el manifest.

5. Diseño técnico

- Controlador: `IrgTFMController.helpdesk_custom()` renderiza `irg_course_portal_tiles.helpdesk_page`.
- Template: `irg_course_portal_tiles.helpdesk_page` usa `<t t-call="website.layout">` y `<t t-call="website_helpdesk.ticket_submit_form"/>` para reusar el formulario existente.
- Vistas: `irg_course_portal_tiles_views.xml` modifica el tile mediante `t-set` y `t-att-href` para apuntar a `/helpdesk/atencion-al-cliente-1`.
- Dependencias: `website_helpdesk`, `openeducat_web`, `isep_website_custom`.

6. Dependencias (`depends` en `__manifest__`)

- isep_website_custom
- openeducat_web
- website_helpdesk

7. Backwards-compatibility / migración

- No impacta datos. Solo añade vistas y rutas nuevas. Si se desinstala el módulo, el tile volverá a su comportamiento por defecto si existe otra definición.

8. Casos de prueba / criterios de aceptación

- Al actualizar el módulo `irg_course_portal_tiles`, la ruta `/helpdesk/atencion-al-cliente-1` devuelve la página con el titular y el subtítulo en blanco.
- El tile "Atención" en la vista del curso enlaza a `/helpdesk/atencion-al-cliente-1`.
- El formulario `ticket_submit_form` se muestra dentro de la página (si `website_helpdesk` está instalado).
- No hay errores de QWeb ni de importación al instalar/actualizar el módulo.

9. Rollback plan

- Revertir commit(s) asociados al PR/branch: `git revert <commit>` o restaurar desde main branch.
- Desinstalar el módulo desde la interfaz web o con:

```bash
# dentro del contenedor, ejemplo
odoo -d <db> -u base --stop-after-init
# o usar la interfaz para desinstalar irg_course_portal_tiles
```

10. Estimación y responsable

- Estimación: 1h (implementar + test básico en staging).
- Responsable: Equipo iRG / Sebastian Corradini.

---

Changelog corto (implementación 2026-02-27):
- Añadida plantilla `helpdesk_page.xml` con subtítulo para documentación académica.
- Añadida ruta `/helpdesk/atencion-al-cliente-1` en `controllers/main.py`.
- Tile "Atención" apuntando al nuevo URL; reemplazo dinámico de "Cliente" → "Alumno".
- `website_helpdesk` añadido a `depends`.
- Nota: assets SCSS/JS añadidos en `static/src/` pero su registro final en assets está pendiente y será aplicado en PR siguiente.
