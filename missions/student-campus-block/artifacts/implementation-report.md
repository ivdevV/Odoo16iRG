# Informe de implementación — `irg_student_campus_block`

## Objetivo y alcance

Se creó un módulo nuevo para bloquear o restaurar, desde el formulario de `op.student`, el acceso autenticado a Odoo del usuario portal actualmente vinculado al estudiante. No se modificó OpenEduCat ni ningún otro módulo existente.

El bloqueo se implementa mediante `res.users.active = False`. Esto afecta al portal, eLearning, foros y cualquier otro acceso autenticado a la misma instancia Odoo. Moodle no forma parte de esta implementación.

## Arquitectura

El módulo depende únicamente de `openeducat_core` y extiende `op.student` mediante `_inherit`.

- `irg_campus_blocked` es un booleano computado y no almacenado. Su valor es verdadero cuando existe `user_id` y ese usuario está inactivo. El compute usa `active_test=False`, por lo que también puede leer usuarios archivados.
- `action_block_campus_access()` y `action_unblock_campus_access()` son acciones públicas separadas. Ambas delegan en una operación interna idempotente con el estado final explícito.
- Antes de cualquier elevación de permisos se valida en servidor que el operador pertenezca a `group_op_back_office_admin`, que el usuario vinculado exista y que sea portal externo, no interno ni público.
- El único `sudo()` productivo está acotado a la escritura de `active` en el usuario objetivo. `message_post()` se ejecuta con el usuario operador real.
- Solo se publica chatter cuando cambia efectivamente el estado. Repetir la misma acción no genera mensajes duplicados.
- La vista hereda `openeducat_core.view_op_student_form` mediante XPath, sin editar la vista original.

## Archivos del módulo

- `addons-extra/extrairg/irg_student_campus_block/__manifest__.py`: metadatos, versión `16.0.1.0.0`, dependencia y carga de vista.
- `addons-extra/extrairg/irg_student_campus_block/__init__.py`: registro del paquete de modelos.
- `addons-extra/extrairg/irg_student_campus_block/models/__init__.py`: registro de la extensión de estudiante.
- `addons-extra/extrairg/irg_student_campus_block/models/op_student.py`: campo computado, autorización, validación de objetivo, cambio de estado y chatter.
- `addons-extra/extrairg/irg_student_campus_block/views/op_student_view.xml`: botones, confirmaciones y ribbon.
- `addons-extra/extrairg/irg_student_campus_block/tests/__init__.py`: descubrimiento obligatorio de tests Odoo.
- `addons-extra/extrairg/irg_student_campus_block/tests/test_student_campus_block.py`: suite funcional, de seguridad, integración opcional y vista.

No se añade `ir.model.access.csv` porque el módulo no crea modelos ni concede accesos nuevos. La restricción se aplica al grupo de la vista y se vuelve a comprobar dentro del método de servidor.

## Configuración e instalación

No existen parámetros de sistema, cron, datos maestros ni secretos nuevos. Basta con que `addons-extra/extrairg` esté incluido en `addons_path`.

Instalación local en la base de pruebas:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_student_campus_block --stop-after-init
```

Actualización posterior:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_student_campus_block --stop-after-init
```

En un worktree, un contenedor ya creado conserva su volumen anterior. Para probar un overlay sin recrear el servicio se debe usar un contenedor efímero con `docker compose ... run --rm --no-deps odoo_local ...`; `exec` no cambia los mounts del contenedor existente.

## Uso

1. Acceder a OpenEduCat como administrador de back-office.
2. Abrir el formulario del estudiante.
3. Si tiene un usuario portal activo, pulsar «Bloquear acceso campus» y confirmar.
4. Si el usuario está inactivo, pulsar «Desbloquear acceso campus» y confirmar.

Los botones no aparecen si no existe `user_id`. El ribbon «Campus bloqueado» se muestra cuando el estudiante está activo y su usuario portal está bloqueado. Si el propio estudiante está archivado, prevalece el ribbon base «Archived» y no se muestran ambos simultáneamente.

Las acciones son idempotentes: una petición repetida de bloqueo deja el usuario bloqueado, y una petición repetida de desbloqueo lo deja activo, sin chatter adicional.

## Permisos y errores controlados

- Solo `openeducat_core.group_op_back_office_admin` puede ejecutar las acciones.
- Un faculty recibe `AccessError` incluso si intenta invocar el método por JSON-RPC.
- Un estudiante sin usuario vinculado produce `UserError`.
- Un objetivo inexistente o que no sea portal externo produce `UserError`.
- No se permite archivar mediante estas acciones un usuario interno o público.

## Autenticación y sesiones

Al bloquear, Odoo marca el usuario como inactivo. La validación HTTP demostró que:

- una sesión portal ya autenticada recibe una redirección `303` a `/web/login` en la siguiente petición;
- una nueva autenticación no obtiene `uid` mientras el usuario está bloqueado;
- tras desbloquear, el usuario vuelve a autenticarse y `/my/home` responde `200`.

El módulo no borra físicamente registros de sesión ni afirma que Redis sea purgado. El efecto garantizado es el rechazo de la autenticación y de la sesión en la siguiente petición procesada por Odoo.

## Moodle

Moodle está expresamente fuera de alcance. El manifest no declara módulos Moodle, el código no llama APIs de Moodle y las confirmaciones de la interfaz avisan de que Moodle no se ve afectado. Si se requiere bloqueo coordinado, debe diseñarse como una fase independiente con su propia integración, manejo de errores y política de reversión.

## Pruebas realizadas

La validación independiente, ejecutada contra `docker-compose.local.yml` y el overlay del worktree, obtuvo:

- 11/11 métodos Odoo, 0 fallos y 0 errores;
- upgrade del módulo y carga de los 718 módulos instalados;
- bloqueo, desbloqueo y compute real;
- idempotencia y ausencia de chatter duplicado;
- autoría real del chatter;
- rechazo de faculty por ORM y por JSON-RPC real;
- rechazo de objetivos internos y públicos/no portal;
- ausencia de usuario vinculado;
- estructura de botones, grupos, confirmaciones y ribbon;
- tabla de verdad de ribbons Campus/Archived sin solapamiento;
- compileall, AST, manifest, XML y Ruff;
- alcance exacto de `sudo()` y ausencia de integración Moodle;
- login, sesión existente y restauración mediante HTTP real;
- limpieza de usuarios desechables y restauración del contenedor al mount del checkout principal.

La evidencia final está referenciada en `missions/student-campus-block/verification.json` y en los archivos `artifacts/final-validation-*.log`.

## Rematrícula y limitaciones conocidas

Se caracterizaron dos escenarios cuando el módulo opcional `irg_sale_manual_confirmation_wizard` está instalado:

1. Si el usuario bloqueado sigue vinculado al estudiante, `_ensure_portal_user()` reutiliza ese vínculo y el usuario permanece inactivo. La rematrícula no lo reactiva.
2. Si el usuario archivado fue desvinculado del estudiante, la búsqueda actual del wizard no usa `active_test=False`. Intenta crear otro usuario con el mismo login y Odoo produce `ValidationError`. El usuario original permanece inactivo y el estudiante continúa sin vínculo.

El segundo caso es un riesgo preexistente del wizard y no se corrige aquí para evitar una dependencia funcional y una ampliación de alcance injustificadas.
