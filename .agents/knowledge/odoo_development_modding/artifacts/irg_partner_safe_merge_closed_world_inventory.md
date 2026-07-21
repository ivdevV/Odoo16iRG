# Safe merge: inventario relacional cerrado y concurrencia

## Contexto

Una consolidación de `res.partner` con relaciones de negocio requiere una frontera explícita: los metadatos sirven para descubrir referencias, no para autorizar transferencias.

## Patrón reutilizable

- Mantener allowlists estáticas para transferir, recalcular, conservar, unir semánticamente o bloquear. Si una referencia persistente al origen no está clasificada y tiene filas, abortar la operación.
- Los barridos genéricos de metadatos deben comprobar que el modelo expone el campo ORM `id` antes de hacer `search(..., order="id")`. Algunos modelos abstractos del registro (por ejemplo, `hr.employee.base`) no tienen `id`; omitir solo esos modelos, no todos los modelos con `_auto = False`, para seguir revisando vistas SQL con filas ORM.
- En confirmaciones concurrentes, bloquear primero los contactos en orden canónico y después las filas del plan en orden estable. Recalcular el inventario y comparar un hash de preview que incluya decisiones y relaciones antes de escribir.
- Tratar `SerializationFailure` como comportamiento transaccional de Odoo: dejar que `odoo.service.model.retrying` reintente la petición. Las pruebas deben usar cursores independientes y cubrir tanto doble confirmación del mismo sentido como la inversa.

## Motivo

El inventario cerrado evita que una nueva relación de un módulo instalado se transfiera por accidente. El guard de `id` conserva el análisis de modelos persistentes y evita un fallo de runtime durante el preview. El orden de locks, el hash y la restricción única de auditoría mantienen la operación atómica e idempotente.
