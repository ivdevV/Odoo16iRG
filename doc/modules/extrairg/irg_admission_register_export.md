# irg_admission_register_export

**Categoría:** extrairg
**Versión:** 16.0.1.1.0
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
- Columnas: Nº Aplicación, Nombre, Email, Teléfono, Móvil, Fecha Aplicación, Fecha Admisión, Curso, Lote, Estado, Nacionalidad (`op.student.nationality`).
- Si la admisión no tiene alumno o el alumno no tiene nacionalidad, la celda queda vacía.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.admission.export.wizard` (nuevo) | Nuevo | Registro de admisiones, formato, filtros |

## Vistas y UI

- `wizard/admission_export_wizard_view.xml` — formulario del wizard de exportación.

## Notas técnicas

- Requiere `security/ir.model.access.csv` por el modelo del wizard.
- CSV y XLSX comparten `_COLUMNS` / `_get_rows`. No se exporta `citizenship_country_id`.

## Limitaciones

- La nacionalidad sale del alumno vinculado (`student_id`), no del país de dirección del contacto.
- Hace falta actualizar el módulo a `16.0.1.1.0` para que la columna aparezca.

## Pruebas

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d <dbname> \
  -u irg_admission_register_export --test-enable \
  --test-tags=/irg_admission_register_export --stop-after-init \
  --http-port=8099 --log-level=test --workers=0
```

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
