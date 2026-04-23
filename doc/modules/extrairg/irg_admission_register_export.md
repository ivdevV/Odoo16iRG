# irg_admission_register_export

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `openeducat_admission`

---

## ¿Qué hace este módulo?

Permite exportar todas las admisiones de un registro de admisiones a CSV o XLSX directamente desde el menú de acciones del registro. Facilita la extracción de datos de matriculaciones para reporting externo o análisis.

## Funcionalidades principales

- Wizard de exportación accesible desde el menú de acciones del registro de admisiones.
- Soporte de exportación a CSV y XLSX.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.admission.export.wizard` (nuevo) | Nuevo | Registro de admisiones, formato, filtros |

## Vistas y UI

- `wizard/admission_export_wizard_view.xml` — formulario del wizard de exportación.

## Notas técnicas

- Requiere `security/ir.model.access.csv` por el modelo del wizard.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_admission_register_export \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_admission_register_export \
    --stop-after-init --db_host=pgodoo_latest
```
