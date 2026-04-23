# looker_sql_connector

**Categoría:** extrairg
**Versión:** 2.0
**Licencia:** OPL-1
**Instalable:** Sí
**Autor:** TechFinna
**Precio:** $150
**Depende de:** `base`

---

## ¿Qué hace este módulo?

Amplía el `looker_connector` con capacidades de consulta SQL directa desde Looker Studio. Permite ejecutar queries SQL personalizadas sobre la base de datos de Odoo para crear métricas avanzadas que no son posibles con el conector estándar.

## Funcionalidades principales

- Consultas SQL personalizadas desde Google Looker Studio.
- Amplía las capacidades del `looker_connector` con SQL directo.

## Notas técnicas

- Módulo comercial complementario de `looker_connector`.
- Requiere permisos adecuados para evitar accesos no autorizados a datos sensibles.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i looker_sql_connector \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u looker_sql_connector \
    --stop-after-init --db_host=pgodoo_latest
```
