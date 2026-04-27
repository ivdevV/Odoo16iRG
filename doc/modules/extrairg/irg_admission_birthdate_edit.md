# irg_admission_birthdate_edit

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `openeducat_admission`

---

## ¿Qué hace este módulo?

Elimina la condición de solo lectura del campo `birth_date` en `op.admission`, haciéndolo editable independientemente del estado de la admisión. En Odoo estándar, la fecha de nacimiento se vuelve de solo lectura en ciertos estados del proceso de admisión.

## Funcionalidades principales

- Redefine el campo `birth_date` en `op.admission` sin la restricción `readonly`.
- Sin cambios de vista; la modificación es a nivel de modelo.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.admission` | Herencia | `birth_date` sin restricción readonly |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_admission_birthdate_edit \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_admission_birthdate_edit \
    --stop-after-init --db_host=pgodoo_latest
```
