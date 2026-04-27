# irg_portal_placeholder_safe

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `portal`

---

## ¿Qué hace este módulo?

Corrige errores JavaScript que se producen cuando los atributos `data-placeholder_count` de las plantillas del portal tienen valores nulos o indefinidos. Añade valores por defecto para los placeholders del portal, previniendo excepciones silenciosas en el frontend.

## Funcionalidades principales

- Override de plantillas del portal con valores por defecto en `data-placeholder_count`.
- Previene errores JS en el portal cuando no hay datos de conteo.

## Vistas y UI

- `views/portal_templates.xml` — override de templates del portal.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_portal_placeholder_safe \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_portal_placeholder_safe \
    --stop-after-init --db_host=pgodoo_latest
```
