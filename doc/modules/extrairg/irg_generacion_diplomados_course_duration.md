# irg_generacion_diplomados_course_duration

## Proposito

Modulo Odoo 16 que anade al curso los datos de duracion que se imprimen en los diplomas de diplomados:

- Horas del Diplomado.
- ECTS del Diplomado.

El objetivo es evitar que el PDF muestre `0 horas` cuando el diploma se genera desde el portal o desde el wizard de generacion.

## Campos Aniadidos

Modelo: `op.course`

| Campo | Tipo | Uso |
| --- | --- | --- |
| `irg_diplomado_duration_hours` | Integer | Horas impresas en el diploma |
| `irg_diplomado_duration_ects` | Float | Creditos ECTS impresos en el diploma |

Los campos se muestran en la pestana `Asignaturas Diplomado`, dentro del bloque `Datos del Diploma`.

## Integraciones

### Wizard de generacion

Al seleccionar un curso en `irg.diplomado.wizard`, el modulo precarga:

- `duration_hours` desde `course.irg_diplomado_duration_hours`.
- `duration_ects` desde `course.irg_diplomado_duration_ects`.

### Portal de descarga directa

`irg_diplomado_portal_request` copia esos campos al crear el `irg.diplomado.registry` desde el portal. Despues `action_reprint()` usa los valores del registro para pintar el PDF.

## Validacion

Comando ejecutado:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_generacion_diplomados_course_duration -u irg_diplomado_portal_request --test-enable --test-tags /irg_generacion_diplomados_course_duration,/irg_diplomado_portal_request --stop-after-init --http-port=8099 --log-level=test
```

Resultado: `0 failed, 0 error(s)`.
