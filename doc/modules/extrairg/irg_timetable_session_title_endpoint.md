# irg_timetable_session_title_endpoint

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `irg_timetable_subject_prefix`, `irg_op_session_class_title`, `isep_time_link_url`

---

## ¿Qué hace este módulo?

Módulo de integración que une la lógica de títulos de clase (`irg_op_session_class_title`) con el prefijo de código de asignatura (`irg_timetable_subject_prefix`) y el sistema de enlace a URL de sesión (`isep_time_link_url`). Garantiza que el endpoint del calendario portal muestre títulos completos y correctos para cada sesión.

## Funcionalidades principales

- Integración de prefijo de código + nombre de clase en el título del endpoint de sesiones.
- Sin modelos ni vistas propias; es un módulo de orquestación/integración.

## Notas técnicas

- Módulo "pegamento" sin archivos de datos propios; su función es garantizar el orden de dependencias.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_timetable_session_title_endpoint \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_timetable_session_title_endpoint \
    --stop-after-init --db_host=pgodoo_latest
```
