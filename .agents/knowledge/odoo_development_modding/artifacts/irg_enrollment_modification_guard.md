# irg_enrollment_modification_guard

## Patrón reutilizable

Una solicitud de cambio de matrícula debe capturar en servidor únicamente los
campos que afecta. Antes de cada visto se bloquean la solicitud, la matrícula,
el pedido y las líneas relevantes; los conflictos se registran fuera del
savepoint como bloqueo permanente. Las líneas de venta deben compartir un
fence de la fila `sale.order` para cubrir altas y fantasmas bajo
`REPEATABLE READ`.

Los defaults de contexto y `ir.default` no son una fuente confiable para
campos de estado, aprobadores o snapshot. El `create()` debe neutralizarlos y
fijar explícitamente los valores técnicos antes de delegar al modelo base.

## Motivo

La protección solo en botones permite mutaciones por RPC y una comprobación
solo de filas existentes no cubre una línea añadida simultáneamente. El fence
del pedido serializa esa colección sin ampliar ACL; la lectura financiera
académica se limita al vínculo solicitado, mantiene reglas y compañías y no
expone los valores en el mensaje de conflicto.
