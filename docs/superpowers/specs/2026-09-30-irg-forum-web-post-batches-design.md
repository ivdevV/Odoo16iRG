# Selector web de lotes al crear una publicación de foro

## Objetivo

Un usuario interno puede elegir, en el formulario web de alta de un tema de foro, los lotes que podrán ver esa publicación. La selección se guarda en `forum.post.visibility_batch_ids`, el mismo campo que la ficha de backend muestra como «Lotes que pueden visualizar».

Si no marca ningún lote, el campo queda vacío y la publicación la ve quien ya puede entrar en ese foro. Si marca uno o varios, solo los alumnos de esos lotes la ven.

## Alcance

Módulo nuevo `irg_forum_web_post_batches`. No modifica módulos existentes.

Depende de `website_forum`, `irg_forum_batch_visibility`, `openeducat_core` y `openeducat_admission`. La admisión hace falta porque el cálculo de lotes efectivos del usuario consulta `op.admission`.

No añade campos. No cambia `excluded_visibility_batch_ids`. No cambia las reglas de visibilidad del foro ni el envío de correo: el filtro de destinatarios que ya aplica `irg_forum_email_notify` lee `visibility_batch_ids` después del `create`. Por eso los lotes tienen que estar en los valores de creación, no en un `write` posterior.

Los administradores de sistema siguen viendo todas las publicaciones. Ese bypass ya existe en `_is_visible_for_user` y este módulo no lo cambia.

## Quién ve el selector

El selector se renderiza solo si se cumplen las tres condiciones:

- el usuario tiene el grupo `base.group_user`;
- el foro tiene `irg_course_id`;
- ese curso tiene al menos un lote activo.

Un usuario portal no ve las casillas. El formulario de respuesta tampoco las muestra. El alta de un tema nuevo es la única pantalla web afectada: la plantilla `website_forum.new_question`.

## Lotes que aparecen

La lista son los `op.batch` activos cuyo `course_id` es el `irg_course_id` del foro. `op.batch` no tiene `state`; el filtro de activo es `('active', '=', True)`.

No se limita a los lotes ya marcados en el foro. El origen es el curso de OpenEduCat vinculado al foro.

## Escritura

La ruta `POST /forum/<foro>/new` se hereda. El método de Odoo 16 es `post_create`.

Si el usuario es interno, el controlador lee los ids enviados, conserva solo los que pertenecen a la lista permitida de ese foro y los pone en el contexto `irg_visibility_batch_ids`. Después llama a `super()`.

Si el usuario no es interno, el controlador no lee ese parámetro y no pone el contexto.

`forum.post.create` de este módulo, antes de `super()`, copia ese contexto al campo `visibility_batch_ids` con el comando `(6, 0, ids)` cuando el valor creado no tiene `parent_id`. Una respuesta no recibe lotes aunque el contexto exista.

El contexto vacío o ausente no escribe el campo. Así, un alta sin casillas marcadas deja `visibility_batch_ids` vacío.

## Rechazo en servidor

La restricción visual no autoriza el dato. El servidor descarta cualquier id que no sea un lote activo del curso del foro. Si después de filtrar no queda ninguno, el campo queda vacío.

Un portal que envíe ids en el POST no los aplica. Un id de otro curso, inactivo o inexistente tampoco se guarda.

No se usa `sudo()` para ampliar los lotes que el usuario puede asignar.

## Pruebas

Pruebas de módulo, sin depender del orden de carga frente a `irg_forum_email_notify`:

- un usuario interno crea un tema con dos lotes activos del curso y el post guarda esos dos ids;
- un usuario interno crea un tema sin lotes y `visibility_batch_ids` queda vacío;
- un id de otro curso, inactivo o desconocido no se guarda;
- un usuario portal que envía ids deja el campo vacío;
- una respuesta no copia los lotes del contexto.

La validación de la misión incluye el gate E2E porque el cambio toca plantilla web y controlador HTTP. Se ejecuta después de que las pruebas de módulo pasen.

## Fuera de alcance

- Elegir lotes al responder.
- Mostrar el selector a usuarios portal.
- Editar los lotes desde la página web del tema ya publicado.
- Cambiar el envío síncrono de correo a n8n.
- Filtrar por lotes inactivos o por la fecha de corte de Moodle del foro.
