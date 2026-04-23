# irg_crm_extensions

**Categoría:** extrairg
**Versión:** 16.0.1.0.3
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `crm`

---

## ¿Qué hace este módulo?

Añade extensiones personalizadas al CRM de IRG: campo de seguimiento del comercial anterior asignado al lead y fecha de reactivación del lead. Facilita el seguimiento del historial de asignaciones comerciales y la planificación de recontactos.

## Funcionalidades principales

- Campo `last_user_id` — comercial anterior asignado al lead.
- Campo `fecha_reactivacion` — fecha planificada para reactivar el contacto con el lead.
- Vista de CRM actualizada con estos campos.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `crm.lead` | Herencia | `last_user_id`, `fecha_reactivacion` |

## Vistas y UI

- `views/crm_lead.xml` — campos adicionales en el formulario del lead.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_crm_extensions \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_crm_extensions \
    --stop-after-init --db_host=pgodoo_latest
```
