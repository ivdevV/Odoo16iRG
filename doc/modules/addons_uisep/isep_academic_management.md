# isep_academic_management

**Categoría:** addons_uisep
**Versión:** 1.6.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `web`, `openeducat_admission`, `openeducat_core`, `isep_elearning_custom`, `isep_control_escolar`, `isep_record_request_extended`

---

## ¿Qué hace este módulo?

Hub de gestión académica. Centraliza las operaciones administrativas sobre alumnos y admisiones: gestión del expediente del alumno, control escolar, solicitudes de documentos (certificados, títulos) y el flujo de control de escolar completo. Es el módulo principal de la secretaría académica de ISEP.

## Funcionalidades principales

- Gestión centralizada del expediente del alumno.
- Control escolar (matrícula, cambios de lote, bajas).
- Integración con el flujo de solicitudes de documentos.
- Vistas de gestión masiva de admisiones.
- Acciones de servidor para procesos académicos masivos.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.admission` | Herencia | Campos de expediente, control escolar |
| `op.student` | Herencia | Vista de gestión académica |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_academic_management \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_academic_management \
    --stop-after-init --db_host=pgodoo_latest
```
