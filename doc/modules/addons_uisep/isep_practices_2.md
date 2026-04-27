# isep_practices_2

**Categoría:** addons_uisep
**Versión:** 16.7
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `base`, `mail`, `portal`, `openeducat_core`, `openeducat_fees`, `openeducat_admission`, `website`, `sign`, `base_location`, `base_location_geonames_import`

---

## ¿Qué hace este módulo?

Segunda versión del módulo de prácticas externas. Versión mejorada con nuevas funcionalidades: crons de recordatorio, soporte para más tipos de convenio, integración con GeoNames para gestión de ubicaciones de empresas, y mejoras en el flujo del portal del alumno.

## Funcionalidades principales

- Todas las funcionalidades de `isep_practices` (v1).
- Crons de recordatorio de tareas de prácticas.
- Soporte para múltiples tipos de convenio de prácticas.
- Integración con GeoNames para ubicaciones de empresas.
- Portal del alumno mejorado para seguimiento de prácticas.
- Flujo de estados ampliado.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `isep.practices` (herencia/nuevo) | Nuevo/Herencia | Alumno, empresa, tutor, estado, convenio, ubicación |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_practices_2 \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_practices_2 \
    --stop-after-init --db_host=pgodoo_latest
```
