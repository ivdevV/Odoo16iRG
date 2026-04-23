# irg_practice_center_restrict

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_practices_2`

---

## ¿Qué hace este módulo?

Oculta la lista de centros de prácticas en el portal del alumno. Los centros de prácticas son información interna de gestión y no deben ser visibles para los alumnos en su portal personal.

## Funcionalidades principales

- Override de la plantilla del portal de prácticas para ocultar la sección de centros.

## Vistas y UI

- `views/templates.xml` — override del template del portal de prácticas.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_practice_center_restrict \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_practice_center_restrict \
    --stop-after-init --db_host=pgodoo_latest
```
