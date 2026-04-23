# mauit_roles

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** No especificado
**Depende de:** `crm`, `contacts`, `sales_team`

---

## ¿Qué hace este módulo?

Define roles personalizados para la plataforma Mauit dentro del contexto de CRM, contactos y equipos de ventas. Permite asignar perfiles específicos de acceso y funcionalidad a los diferentes roles de usuario en el entorno de Mauit integrado con Odoo.

## Funcionalidades principales

- Roles personalizados de Mauit en CRM.
- Integración con equipos de ventas y contactos.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i mauit_roles \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u mauit_roles \
    --stop-after-init --db_host=pgodoo_latest
```
