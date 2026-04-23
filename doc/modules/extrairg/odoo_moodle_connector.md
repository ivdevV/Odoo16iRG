# odoo_moodle_connector

**Categoría:** extrairg
**Versión:** 1.0
**Licencia:** OPL-1
**Instalable:** Sí
**Autor:** WoadSoft
**Precio:** €200
**Depende de:** `base`, `contacts`, `calendar`, `website_slides`, `hr`

---

## ¿Qué hace este módulo?

Conector de sincronización entre Odoo y Moodle (LMS). Permite sincronizar usuarios, cursos, matrículas y calendarios entre ambas plataformas, permitiendo usar Moodle como plataforma de aprendizaje mientras Odoo gestiona la parte administrativa (matrículas, pagos, alumnos).

## Funcionalidades principales

- Sincronización de usuarios Odoo ↔ Moodle.
- Sincronización de cursos Odoo (`website.slides`) ↔ Moodle.
- Sincronización de matrículas de alumnos.
- Sincronización de eventos de calendario.
- Integración con el módulo `hr` para empleados/docentes.

## Notas técnicas

- Módulo comercial (OPL-1) de WoadSoft.
- Requiere configurar las credenciales de la API de Moodle (token de acceso).

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i odoo_moodle_connector \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u odoo_moodle_connector \
    --stop-after-init --db_host=pgodoo_latest
```
