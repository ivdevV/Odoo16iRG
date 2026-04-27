# isep_op_session

**Categoría:** addons_uisep
**Versión:** 16.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `base`, `openeducat_lesson`, `openeducat_timetable`, `isep_elearning_custom`

---

## ¿Qué hace este módulo?

Proporciona un wizard de planificación masiva de sesiones académicas. Permite generar todas las sesiones de un lote/período con un solo clic, definiendo el horario semanal, las fechas de inicio/fin y los docentes por asignatura.

## Funcionalidades principales

- Wizard de creación masiva de sesiones académicas.
- Configuración de horario semanal (días y horas por asignatura).
- Generación automática de sesiones para todo el período académico.
- Exclusión de festivos y períodos de vacaciones.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `isep.op.session.wizard` (nuevo) | Nuevo | Período, lote, horario, fechas |

## Vistas y UI

- Wizard de planificación de sesiones desde el lote o timetable.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_op_session \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_op_session \
    --stop-after-init --db_host=pgodoo_latest
```
