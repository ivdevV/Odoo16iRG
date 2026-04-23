# looker_connector

**Categoría:** extrairg
**Versión:** 2.0.4
**Licencia:** OPL-1
**Instalable:** Sí
**Autor:** TechFinna
**Precio:** $287
**Depende de:** `base`, `web`

---

## ¿Qué hace este módulo?

Conector oficial de Odoo con Google Looker Studio (anteriormente Google Data Studio). Permite crear informes y dashboards en Looker Studio usando datos directamente desde Odoo, sin necesidad de exportar datos manualmente.

## Funcionalidades principales

- Conector nativo Odoo → Google Looker Studio.
- Acceso a datos de cualquier modelo de Odoo desde Looker Studio.
- Autenticación y permisos gestionados desde Odoo.

## Notas técnicas

- Módulo de terceros comercial (OPL-1), no modificable bajo licencia libre.
- No forma parte del stack custom IRG/ISEP; es un conector externo adquirido.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i looker_connector \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u looker_connector \
    --stop-after-init --db_host=pgodoo_latest
```
