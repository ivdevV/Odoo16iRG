# Patrón reutilizable: bloquear acceso portal desde un modelo de negocio

## Contexto

En Odoo 16, `op.student.user_id` enlaza el estudiante con `res.users`. Para impedir realmente el login sin dejar una cuenta autenticable, el mecanismo usado por `irg_student_campus_block` es archivar el usuario mediante `active=False`, no retirar únicamente `base.group_portal`.

## Decisiones de diseño

1. Usar acciones explícitas `block` y `unblock`, no un toggle. Una petición repetida u obsoleta debe converger al estado solicitado y no invertir el estado fijado por otro operador.
2. Aplicar doble control de autorización: `groups` en la vista para UX y `has_group()` en el servidor para proteger ORM/JSON-RPC.
3. Resolver usuarios archivados con `active_test=False` y confirmar `.exists()` antes de escribir.
4. Validar el objetivo antes de `sudo()`: debe tener `base.group_portal` y no `base.group_user`. Un usuario público/no portal también se rechaza.
5. Limitar `sudo()` al write mínimo de `res.users.active`. El registro de chatter debe ejecutarse sin sudo para conservar el autor real.
6. Publicar chatter solo cuando el estado cambia; la idempotencia también evita ruido de auditoría.
7. Modelar el estado visual como compute no almacenado dependiente de `user_id` y `user_id.active`, evitando una segunda fuente de verdad.
8. Si se añade un ribbon a una vista que ya posee otro, modelar explícitamente la precedencia. En este caso «Campus bloqueado» se oculta cuando `op.student.active=False`, dejando visible únicamente «Archived».

## Patrón de seguridad

Orden recomendado dentro de la acción:

1. comprobar el grupo del operador;
2. obtener el identificador del usuario actualmente vinculado;
3. recuperar el usuario con `active_test=False` y `.exists()`;
4. comprobar portal externo/no interno;
5. comparar el estado deseado para mantener idempotencia;
6. ejecutar únicamente `target_user.sudo().write({'active': desired})`;
7. publicar el chatter con el recordset del operador real.

La restricción visual nunca sustituye la autorización server-side. Una prueba HTTP debe invocar `/web/dataset/call_kw` con un usuario no autorizado y comprobar tanto `error.data.name == 'odoo.exceptions.AccessError'` como que `active` no cambió, leído con `active_test=False`.

## Semántica de sesión

`res.users.active=False` impide nuevas autenticaciones y provoca que una sesión existente sea rechazada en la siguiente petición. No debe documentarse como eliminación física inmediata de la sesión Redis salvo que exista evidencia específica de esa operación. La afirmación segura es: «el acceso queda bloqueado en la siguiente petición procesada por Odoo».

## Integraciones opcionales sin dependencia funcional

Para caracterizar convivencia con un módulo opcional sin añadirlo a `depends`:

- detectar la extensión con `hasattr(env['modelo'], 'metodo_opcional')`;
- usar `skipTest` si no está instalada;
- preferir `model.new({...})` cuando solo se prueba un método y persistir el registro obligaría a crear curso, register u otros datos ajenos al escenario.

Esto permitió probar `_ensure_portal_user()` de `irg_sale_manual_confirmation_wizard` sin convertirlo en requisito de instalación.

## Gotcha de rematrícula

- Usuario archivado aún vinculado: el wizard conserva el vínculo y no reactiva el usuario.
- Usuario archivado y desvinculado: el wizard busca usuarios sin `active_test=False`, no encuentra el archivado e intenta crear otro con el mismo login. Odoo eleva `ValidationError` por login duplicado.

Este segundo caso pertenece al módulo que asegura el usuario portal. Corregirlo desde el módulo de bloqueo introduciría acoplamiento y responsabilidad cruzada. Una solución futura debe modificar aquel flujo mediante un nuevo módulo heredado y cubrir búsqueda por partner/login con `active_test=False`, política explícita de relink y prohibición de reactivar silenciosamente una cuenta bloqueada.

## Gotcha de Docker Compose con worktrees

`docker compose exec` utiliza los mounts con los que se creó el contenedor; añadir un overlay al comando no reemplaza el volumen de un contenedor ya existente. Para validar un worktree sin recrear el servicio persistente, usar `docker compose -f base -f overlay run --rm --no-deps ...`. Después de pruebas que sí recreen el servicio, restaurar y verificar el mount del checkout principal.

## Evidencia de referencia

- Misión: `missions/student-campus-block/`.
- Resultado final: `verification.json` con `status: passed`.
- Suite: 11/11 métodos, 0 fallos, 0 errores.
- HTTP: denegación faculty por JSON-RPC, redirección `303` de sesión bloqueada y restauración completa tras desbloqueo.
