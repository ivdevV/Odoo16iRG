# irg_gradebook_autoload_subjects

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_gradebook`

---

## ¿Qué hace este módulo?

Puebla automáticamente las asignaturas de la libreta de calificaciones (`app.gradebook.student`) al crear la libreta, tomando la lista de asignaturas del curso asociado. Sin este módulo, las asignaturas debían añadirse manualmente una a una.

## Funcionalidades principales

- Override del método `create` de `app.gradebook.student` para auto-cargar asignaturas.
- Carga de asignaturas según la lista del curso de la admisión.
- Sin vistas adicionales; la carga es automática al crear la libreta.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `app.gradebook.student` | Herencia | Auto-carga de asignaturas al crear |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_gradebook_autoload_subjects \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_gradebook_autoload_subjects \
    --stop-after-init --db_host=pgodoo_latest
```
