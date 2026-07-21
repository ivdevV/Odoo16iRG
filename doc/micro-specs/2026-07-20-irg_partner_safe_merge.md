# Micro-spec: IRG Partner Safe Merge

## Estado

Aprobada por el usuario el 2026-07-20 mediante el plan conversacional de “Fusión segura de contactos duplicados”, con la corrección de que el contacto maestro de Camila es `1373479`.

## Objetivo

Consolidar exactamente dos contactos personales que representan a la misma persona, sin fusionar sus leads, sin eliminar registros de negocio y archivando el origen como respaldo auditable.

## Activación

- Módulo instalable `irg_partner_safe_merge`.
- Acción contextual **Fusión segura** desde Contactos.
- Sin cron, detección automática ni cambios de datos al instalar.
- Apertura, preview y confirmación verifican en servidor `base.group_system` y exactamente dos IDs distintos.

## Invariantes

- Maestro y origen distintos; maestro activo; origen activo antes de ejecutar.
- Ambos son personas, no compañías, no mantienen relación padre/hijo y tienen compañía compatible.
- Coinciden por email normalizado, teléfono saneado o documento.
- El origen no está fusionado; no se admiten autofusión, ciclos ni cadenas hacia un origen archivado.
- El origen termina `active=False` y `irg_merged_into_partner_id=master`; `ondelete='restrict'`; no puede eliminarse.
- Los cuatro leads de Camila preservan ID, cantidad, etapa, responsable, mensajes y actividades; solo cambia `crm.lead.partner_id` cuando apunta al origen.
- Ninguna operación llama al `_merge()` estándar, hace `cr.commit()` ni borra una relación para resolver un error.

## Elección del maestro

La recomendación, nunca ejecución automática, prioriza: suscripción confirmada/activa; venta confirmada; pagos; usuario/estudiante; completitud; antigüedad. El administrador puede invertirla antes del preview final.

Para Camila:

- Maestro `res.partner(1373479)` por `sale.order(2806)` confirmado y su `sale.subscription.schedule(8662)`.
- Origen `res.partner(53089)`.
- Trasladar `res.users(1396)` y `op.student(1180)` al maestro conservando IDs y coherencia.

## Campos escalares

Solo se ofrecen decisiones sobre campos de identidad/contacto declarados en una allowlist estática: nombre, email, teléfono, móvil, VAT/tipo de identificación, fecha de nacimiento, idioma, país/estado, ciudad, código postal, calle/calle2 y banderas de estudiante aplicables. Vacíos del maestro se rellenan; divergencias no vacías requieren elección. Campos computados, relacionados, x2many, binarios, tokens, propiedades por compañía y campos técnicos no se escriben. Sus valores permanecen en el origen archivado y en la auditoría descriptiva.

## Política cerrada de relaciones

El inventario de metadatos detecta referencias, pero solo la siguiente allowlist autoriza acciones. Toda referencia no clasificada y con filas del origen bloquea el merge.

### Transferir por ORM

- `res.users.partner_id`, únicamente uno en origen y ninguno en maestro.
- `op.student.partner_id`, únicamente uno en origen y ninguno en maestro; validar coherencia con `op.student.user_id` y `res.users.partner_id`.
- `crm.lead.partner_id`.
- `op.admission.partner_id` y `op.admission.elearning.wizard.partner_id`.
- `appisep.gradebook.summary.student_id`, si el campo no es computed/related en el registro instalado; de lo contrario se reclasifica como recalculado.
- `sale.order.partner_id`, `partner_invoice_id`, `partner_shipping_id`, `student_id`.
- `sale.order.line.student_id`.
- `sale.subscription.schedule.partner_id`, `partner_invoice_id`.
- `slide.channel.partner.partner_id`, solo cuando no exista colisión por canal.
- `voip.phonecall.partner_id`.
- `stripe.subscription.partner_id` cuando exista el modelo y no haya colisión.

### Recalcular, no escribir directamente

- `sale.order.line.order_partner_id` y demás campos related/computed derivados de relaciones transferidas.
- `app.gradebook.student.partner_id` y `app.gradebook.subject.partner_id`, derivados de admisión/estudiante.
- Cualquier campo allowlisted que el registro instalado declare `compute` o `related`, aunque sea stored.

### Conservar apuntando al origen archivado

- Autoría/recepción histórica: `mail.message.author_id`, `mail.notification.res_partner_id`.
- Propiedad histórica de adjuntos: `ir.attachment.partner_id`.
- Firmas: `sign.request.item.partner_id`, `sign.log.partner_id`.
- Tarjetas, tokens y transacciones de pago ya vinculados al maestro se conservan. Si alguno apunta al origen, el merge bloquea para revisión de pagos.

### Referencias polimórficas del propio contacto

Solo se trasladan cuando identifican directamente `res.partner,<origen>`:

- `mail.message(model='res.partner', res_id=origen)`.
- `mail.activity(res_model='res.partner', res_id=origen)`.
- `ir.attachment(res_model='res.partner', res_id=origen)`.
- `mail.followers(res_model='res.partner', res_id=origen)`.
- `ir.model.data(model='res.partner', res_id=origen)` se conserva sobre el origen archivado para mantener estable su identidad externa.

### Unión semántica aprobada

- Categorías de contacto: unión por categoría; una relación idéntica representa el mismo dato.
- Followers del mismo recurso: unir subtipos en el follower del maestro y retirar únicamente la fila relacional redundante después de demostrar igualdad de recurso/partner. No se elimina mensaje, actividad ni adjunto.

### Bloquear

- Cualquier referencia no incluida arriba.
- `res.partner.bank` del origen.
- Facturas, apuntes o pagos contables del origen, especialmente publicados.
- Dos usuarios, dos estudiantes o incoherencia entre usuario y estudiante.
- Colisiones en membresías educativas, gradebooks, admisiones, ventas, suscripciones o cualquier tabla de negocio.

## Concurrencia, autorización e idempotencia

- Validar `base.group_system` en apertura, preview y confirmación; no confiar en `active_ids`, líneas, nombres de campo ni valores del cliente.
- Al confirmar: bloquear contactos en orden ascendente y luego filas allowlisted en orden estable; recalcular identidad, referencias, conflictos y plan completo.
- El hash de preview incluye valores escalares allowlisted, IDs de relaciones y acciones previstas.
- Si cambia el hash, exigir nuevo preview.
- Doble confirmación devuelve la auditoría existente; una restricción única por origen impide dos fusiones.
- ORM es la vía predeterminada. SQL solo para `SELECT ... FOR UPDATE` y catálogo, usando identificadores estáticos o `psycopg2.sql.Identifier` sobre la allowlist.
- Cualquier `IntegrityError` se propaga como error funcional y revierte la petición completa.

## Auditoría

`irg.partner.safe.merge.audit` es inmutable y legible solo por administradores. Se crea con `sudo()` únicamente desde el método autorizado después de completar la operación e incluye actor, fecha, maestro, origen, decisiones, hash y IDs/conteos transferidos. `create` exige entorno `su`; `write` y `unlink` siempre fallan. Un fallo deja datos y auditoría exactamente como antes.

`irg_merged_into_partner_id` solo puede escribirse desde el servicio autorizado con entorno `su`. Una escritura RPC directa del marcador se rechaza. Un contacto con marcador de fusión no puede reactivarse (`active=True`) ni eliminarse, incluso por llamada directa a `write()` o `unlink()`; la protección se aplica server-side.

## Pruebas obligatorias

- Caso Camila equivalente: maestro comercial, traslado de usuario/estudiante, cuatro leads separados, pedidos/admisiones/suscripción intactos.
- RPC manipulado y usuario no administrador.
- RPC directo para modificar el marcador, reactivar o eliminar un origen fusionado.
- Dos usuarios, dos estudiantes, coherencia usuario-estudiante, maestro archivado y origen ya fusionado.
- Relación desconocida, banco, pago/contabilidad y colisiones de negocio bloquean.
- Followers/categorías unen semántica sin perder subtipos.
- Fallos inyectados después de campos, usuario, estudiante, FK, M2M, chatter y archivado verifican rollback total.
- Doble confirmación, merge inverso concurrente y cambio entre preview/confirmación.
