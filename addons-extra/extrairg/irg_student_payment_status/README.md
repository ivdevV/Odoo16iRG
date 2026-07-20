# Estado de pago de alumnos

## Objetivo

`irg_student_payment_status` añade a `op.student` un estado de pago operativo
basado en las facturas académicas vencidas del pagador del alumno. El módulo
permite localizar deuda desde las vistas de alumnos, mantiene una traza en el
chatter y programa el seguimiento cuando un alumno pasa a moroso.

Depende de `openeducat_core` e `irg_student_invoice_payment_link`. No bloquea
el campus, no envía reclamaciones propias y no gestiona cuotas de Stripe.

## Estados

- **Al día**: no hay facturas vencidas.
- **Atrasado**: hay al menos una factura vencida, pero no se alcanza el umbral
  de morosidad.
- **Moroso**: la cantidad de facturas vencidas es igual o superior al umbral.

El estado se almacena en el alumno. La fecha de transición solo se actualiza
cuando el estado cambia; una recomputación sin transición no genera chatter ni
duplica actividades.

## Definición exacta de factura vencida

El cálculo parte del dominio académico proporcionado por
`irg_student_invoice_payment_link`, incluido el pagador alternativo definido
por `irg_student_partner_id`, y exige simultáneamente:

- factura publicada (`state = posted`);
- factura de cliente (`move_type = out_invoice`), por lo que no cuentan las
  rectificativas;
- estado de pago `not_paid` o `partial`;
- fecha de vencimiento estrictamente anterior a
  `hoy - irg_student_payment.grace_days`.

La comparación es estricta. Con 15 días de gracia, una factura que vence
exactamente 15 días antes de hoy todavía no cuenta; empieza a contar al día
siguiente.

## Campos

| Campo | Tipo | Comportamiento |
| --- | --- | --- |
| `irg_payment_status` | Selección almacenada | `al_dia`, `atrasado` o `moroso`; valor inicial `al_dia`, con tracking. |
| `irg_payment_status_date` | Fecha almacenada | Fecha de la última transición; solo lectura y no se copia. |
| `irg_overdue_invoice_count` | Entero calculado | Cantidad live de facturas vencidas. |
| `irg_overdue_amount` | Monetario calculado | Residual live agregado en moneda de compañía. |
| `irg_payment_currency_id` | Moneda calculada | Moneda de la compañía usada por el importe y el chatter. |

Las métricas live leen las facturas con privilegios elevados para que los
usuarios académicos autorizados puedan consultar el resumen sin necesitar
acceso contable. No exponen un recordset editable.

## Parámetros

Los parámetros se gestionan como parámetros del sistema:

| Clave | Valor inicial | Uso y fallback |
| --- | --- | --- |
| `irg_student_payment.moroso_threshold` | `2` | Número mínimo de vencidas para ser moroso. Un valor no entero, cero o negativo usa `2`. |
| `irg_student_payment.grace_days` | `15` | Días de gracia. Un valor no entero o negativo usa `15`; `0` es válido. |
| `irg_student_payment.activity_user_id` | Sin valor inicial | ID de un usuario interno activo al que asignar la actividad. |

Si `activity_user_id` no existe, es inválido, está inactivo o pertenece a un
usuario compartido/portal, se elige de forma determinista un usuario interno
activo del grupo Administrador de back-office de OpenEduCat. Se prioriza
`base.user_admin` y, si no pertenece al conjunto, el usuario con menor ID. Si
no existe ningún candidato válido, no se crea la actividad.

## Cron y recomputación manual

El cron **Actualizar estado de pago de alumnos** está activo, se ejecuta una
vez al día sin límite de repeticiones y procesa como superusuario los alumnos
que tienen partner. Registra en el log las cantidades procesadas, modificadas y
que entraron en morosidad.

La misma ruta de transición se puede invocar manualmente desde Python:

```python
student.action_irg_update_payment_status()
```

No se añade un botón manual específico en la interfaz. La acción está
protegida en servidor: antes de entrar en cualquier cálculo o ruta con
`sudo()`, exige pertenencia a
`openeducat_core.group_op_back_office_admin`, permiso ACL de escritura y que
las reglas de registro permitan escribir todos los alumnos objetivo. Una
restricción meramente visual no sustituye estos controles.

## Ciclo de chatter y actividades

Cada transición publica una nota con estado anterior y nuevo, cantidad de
facturas, residual en moneda de compañía y gracia aplicada. La regularización
de moroso a al día se identifica expresamente en el mensaje.

Al entrar en **Moroso** se programa como máximo una actividad pendiente de
tipo **To Do**, con resumen **Seguimiento de morosidad**, para el gestor
resuelto. Las búsquedas de idempotencia identifican la actividad por tipo,
modelo, alumno y resumen. Al salir de moroso, las actividades propias se
completan mediante `action_feedback()`. Por ello, una reincidencia puede crear
una actividad nueva, mientras que repetir el cálculo sin transición no genera
duplicados.

La actividad usa el mecanismo estándar de `mail.activity`; Odoo puede emitir
su notificación estándar al usuario asignado. El módulo no implementa una
campaña de email adicional.

## Interfaz

- Formulario: ribbon rojo **Moroso**, ribbon ámbar **Atrasado** y smart button
  **Deuda vencida** con cantidad e importe. Los ribbons se ocultan si el alumno
  está archivado.
- Lista: columna opcional **Estado de pago**, filas morosas en rojo y atrasadas
  en ámbar.
- Búsqueda: filtros **Morosos**, **Atrasados** y **Al día**, y agrupación por
  **Estado de pago**.
- Smart button: abre exclusivamente las facturas que cumplen la definición de
  vencida; si solo hay una, abre su formulario.

La validación visual comprobó los filtros, agrupación, columna, decoración,
ribbon, smart button, chatter, actividad y el dominio de las facturas.

## Instalación o actualización local

Desde la raíz del checkout principal, usando siempre
`docker-compose.local.yml`:

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d NOMBRE_BASE \
  -i irg_student_payment_status --stop-after-init
```

Para actualizar una instalación existente, sustituir `-i` por `-u`:

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d NOMBRE_BASE \
  -u irg_student_payment_status --stop-after-init
```

En un worktree cuyo código no esté montado por el compose base, añadir el
overlay del worktree con un segundo `-f` y mantener `run --rm --no-deps` para
no recrear el servicio compartido.

## Pruebas

La suite contiene 15 escenarios. En el worktree de la misión se ejecuta así:

```bash
docker compose \
  -f "/Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/docker-compose.local.yml" \
  -f missions/student-payment-status/docker-compose.worktree.yml \
  run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_student_payment_status --test-enable \
  --test-tags /irg_student_payment_status --without-demo=all \
  --max-cron-threads=0 --stop-after-init --log-level=test
```

El resultado validado es 15 tests, 0 fallos y 0 errores. La base de pruebas se
debe recrear antes del run cuando se necesite una instalación fresca.

## Limitaciones y fase 2

Quedan expresamente fuera de alcance:

- bloqueo automático del campus;
- reclamaciones o campañas de email;
- integración de cuotas o suscripciones Stripe.

`_irg_on_status_change(old_status, new_status)` queda como hook vacío para
extensiones futuras. No se deben añadir efectos de fase 2 al módulo sin su
propio diseño, autorización y pruebas.

Durante instalación y tests aparecen warnings preexistentes de dependencias:
un atributo `digits` desconocido en `irg_sale_order_extended`, labels
duplicados heredados y un tag `report` deprecado. No proceden de este módulo y
no afectan al resultado de su suite.

## Changelog

### 2026-07-16 — 16.0.1.0.0

- Primera versión: estados y métricas de deuda, cron, recomputación protegida,
  chatter, actividad idempotente, vistas y 15 escenarios automatizados.
- Agregación multimoneda corregida a residual en moneda de compañía.
- Cierre de actividades al salir de moroso y soporte de reincidencias.
- Autorización server-side completa para la acción manual.
