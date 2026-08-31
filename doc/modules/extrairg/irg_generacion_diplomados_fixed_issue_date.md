# irg_generacion_diplomados_fixed_issue_date

## Proposito

Fija la fecha impresa en los diplomas de diplomados a **26 de septiembre del año de generación**.

El PDF sigue usando `issue_date` y `_format_issue_date`, que produce
`Barcelona, a 26 de Septiembre de {año}`.

## Comportamiento

- Día y mes: siempre 26 de septiembre.
- Año: el de `fields.Date.context_today` en el momento de generar.
- El asistente `irg.diplomado.wizard` muestra esa fecha en solo lectura y la
  fuerza en `create`/`write`.
- Un `irg.diplomado.registry` creado sin `issue_date` (portal) usa el mismo
  valor por defecto.
- Un registro creado con `issue_date` explícita conserva esa fecha.
- Los diplomas ya emitidos no se reescriben.

## Instalación

Módulo: `irg_generacion_diplomados_fixed_issue_date`.
Dependencia: `irg_generacion_diplomados`.
`auto_install` está desactivado: hay que instalarlo explícitamente en Dev.

## Validación

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_generacion_diplomados_fixed_issue_date --test-enable --test-tags /irg_generacion_diplomados_fixed_issue_date --stop-after-init --http-port=8099 --log-level=test
```
