# irg_crm_extended

**Categoría:** vztech
**Versión:** 0.1
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** DFVZ TECH
**Depende de:** `base`, `crm`

---

## ¿Qué hace este módulo?

Extiende el módulo CRM de Odoo con campos y vistas personalizadas desarrolladas por DFVZ TECH para el entorno de ISEP/IRG. Añade vistas mejoradas del lead/oportunidad y controles de acceso adicionales para los comerciales.

## Funcionalidades principales

- Vistas mejoradas de CRM leads/oportunidades.
- Reglas de acceso adicionales para el equipo comercial.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `crm.lead` | Herencia | Campos y vistas adicionales |

## Vistas y UI

- `views/crm_lead_views.xml` — vistas mejoradas de leads.
- `security/access_current_commercial.xml` — reglas de acceso para comerciales.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_crm_extended \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_crm_extended \
    --stop-after-init --db_host=pgodoo_latest
```
