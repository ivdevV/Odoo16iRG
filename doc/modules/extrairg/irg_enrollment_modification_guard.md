# irg_enrollment_modification_guard

Protege las aprobaciones de `irg_enrollment_modification` contra cambios
posteriores en la matrícula, el pedido o sus líneas.

La solicitud guarda una instantánea server-side de los campos afectados. El
visto académico compara esa instantánea antes de aplicar curso, lote, año o
modalidad. Si hay cambio, la solicitud queda bloqueada permanentemente y se
debe crear una nueva. Cuando interviene el pago, Finanzas comprueba además que
los cambios académicos aprobados siguen vigentes antes de cambiar la forma de
pago.

El módulo protege también las altas, bajas, traslados y ediciones de líneas de
pedido mediante un fence de la fila `sale.order`, incluyendo pedidos obtenidos
por defaults de Odoo. Las solicitudes históricas sin evidencia suficiente se
bloquean de forma conservadora.

No añade permisos ni vistas. Depende de `irg_enrollment_modification`.
