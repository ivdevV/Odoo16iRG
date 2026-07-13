# Auto-enroll robusto: guardarraíl, unicidad por lote y triggers nativos

## Contexto

En Odoo 16, el cron de auto-enroll y el botón manual pueden modificar las mismas filas de
`slide.channel.partner`. Además, cambios en las fechas de `op.subject.to.batch` necesitan
activar el cron con baja latencia sin aumentar la frecuencia de un full-scan.

## Gotcha: denominador del guardarraíl

No se debe calcular un ratio de desmatriculación como
`archived / (activated + archived)`. Si una ejecución pequeña solo archiva una membership,
ese cálculo produce 100% aunque la población bajo control sea grande y bloquea el flujo
normal de fecha pasada/futura.

El patrón validado es:

```python
initial_active_count = sum(1 for active in before.values() if active)
ratio = archived_count / initial_active_count if initial_active_count else 0.0
if ratio > 0.30:
    raise ValidationError(...)
```

El snapshot inicial debe cubrir todas las memberships de los pares alumno/lote de las
admisiones objetivo, incluidas filas históricas visibles con `active_test=False`. Un
savepoint exterior permite revertir todo el run; los savepoints interiores siguen aislando
errores por admisión. El umbral `> 0.30` permite exactamente 30%.

## Patrón: unicidad activa concurrente

Para impedir duplicados confirmados por carreras cron/botón, la garantía debe estar en
PostgreSQL y respetar la identidad académica completa:

```sql
CREATE UNIQUE INDEX ...
ON slide_channel_partner (partner_id, channel_id, batch_id)
WHERE active IS TRUE AND batch_id IS NOT NULL;
```

- Un preflight debe detectar duplicados activos y abortar sin modificar datos.
- El uninstall hook debe retirar el índice con la firma Odoo 16
  `tools.drop_index(cr, index_name, table_name)`.
- Solo se captura la `IntegrityError` cuyo `constraint_name` coincide con ese índice; otras
  violaciones se propagan.
- Las búsquedas para reutilizar archivadas usan `active_test=False`, el `batch_id` actual y
  `order='active DESC, create_date ASC'`.
- La clave por lote permite Homeclass y Online en canales distintos y evita reutilizar una
  membership de otra cohorte.

## Patrón: trigger nativo ante cambios de lote

Los hooks `create/write/unlink` de `op.subject.to.batch` pueden llamar directamente a
`ir.cron._trigger()` cuando cambian `date_from`, `date_to` o `subject_id`. No hace falta una
cola auxiliar ni bloquear `ir_cron`.

Se aceptan triggers temporales redundantes: Odoo ejecuta el cron una vez y limpia los
triggers vencidos. Bajo `REPEATABLE READ`, un trigger confirmado después del snapshot de un
run no es visible para su limpieza final y queda disponible para el siguiente run.

En pruebas concurrentes, registrar el baseline y eliminar exclusivamente los IDs creados
por el test; nunca limpiar todos los triggers del cron.

## Evidencia

Misión `missions/fix-auto-enroll-cron`: suite robusta 27/27, regresiones 13/13, T4.2 manual
pasado/futuro idempotente y rollback confirmado con 4 archivados de 10 activos iniciales.
