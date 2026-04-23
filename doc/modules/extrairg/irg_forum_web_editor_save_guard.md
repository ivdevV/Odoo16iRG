# irg_forum_web_editor_save_guard

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `website_forum`

---

## ¿Qué hace este módulo?

Aplica una sanitización defensiva al guardar posts en el editor del foro. Evita errores producidos por comandos `raw` inválidos en el editor WYSIWYG (OdooEditor) que pueden ocurrir cuando el método `anchor` no está disponible en el contexto de edición del foro.

## Funcionalidades principales

- Guard JavaScript que intercepta comandos `applyRawCommand` inválidos en OdooEditor.
- Previene errores de JavaScript que interrumpirían el guardado del post.
- Sin cambios de modelo ni de interfaz de usuario visible.

## Notas técnicas

- Asset registrado en `web_editor.assets_wysiwyg` para que solo cargue en el contexto del editor.
- Sin archivos de datos Python ni XML de vistas.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_forum_web_editor_save_guard \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_forum_web_editor_save_guard \
    --stop-after-init --db_host=pgodoo_latest
```
