# irg_web_editor_fix

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `web_editor`, `website_forum`

---

## ¿Qué hace este módulo?

Añade una guarda JavaScript en el OdooEditor para evitar errores cuando se ejecutan comandos de anclaje (`anchor`) sobre elementos inválidos o sin el contexto correcto. Sin este fix, ciertos flujos del editor web (especialmente en el foro) lanzaban excepciones silenciosas o visibles.

## Funcionalidades principales

- Guarda JS en el OdooEditor contra comandos de anclaje inválidos.
- Asset incluido en `web_editor.assets_wysiwyg`.

## Notas técnicas

- El asset JS se añade al bundle `web_editor.assets_wysiwyg` para no afectar el frontend general.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_web_editor_fix \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_web_editor_fix \
    --stop-after-init --db_host=pgodoo_latest
```
