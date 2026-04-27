# isep_practices

**Categoría:** addons_uisep
**Versión:** 16.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `base`, `mail`, `portal`, `openeducat_core`, `openeducat_fees`, `openeducat_admission`, `website`, `sign`, `base_location`

---

## ¿Qué hace este módulo?

Primera versión del módulo de prácticas externas para ISEP. Gestiona el proceso de asignación de alumnos a centros de prácticas, incluyendo la firma del convenio de prácticas mediante Sign, seguimiento del progreso y acceso del alumno al portal de prácticas.

## Funcionalidades principales

- Modelo de prácticas externas con flujo de estados.
- Asignación de alumnos a centros de prácticas.
- Firma del convenio de prácticas con Sign.
- Portal del alumno para seguimiento de prácticas.
- Emails de notificación en los cambios de estado.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `isep.practices` (nuevo) | Nuevo | Alumno, empresa, tutor, estado, convenio |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_practices \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_practices \
    --stop-after-init --db_host=pgodoo_latest
```
