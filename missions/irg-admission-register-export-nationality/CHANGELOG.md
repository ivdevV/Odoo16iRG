# irg_admission_register_export

## 16.0.1.1.0 — 2026-09-08

El Excel y el CSV del registro de admisión incluyen la columna **Nacionalidad**, tomada de `op.student.nationality` (`student_id.nationality`). Si no hay alumno o no hay valor, la celda queda vacía.

## Uso

Acción **Exportar Admisiones** en el formulario de `op.admission.register`. Formato por defecto: XLSX.

## Actualización

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d <dbname> \
  -u irg_admission_register_export --stop-after-init
```

## Pruebas

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d <dbname> \
  -u irg_admission_register_export --test-enable \
  --test-tags=/irg_admission_register_export --stop-after-init \
  --http-port=8099 --log-level=test --workers=0
```
