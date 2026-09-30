# irg_forum_web_post_batches

Un usuario interno puede marcar, al crear un tema en la web del foro, los lotes que podrán ver esa publicación. La selección se guarda en **Lotes que pueden visualizar** (`forum.post.visibility_batch_ids`).

## Uso

En el formulario web de alta de un tema, a la derecha del cuadro de descripción, aparecen los lotes activos del curso de OpenEduCat vinculado al foro (`irg_course_id`).

- Sin ninguna casilla marcada, la publicación la ve quien ya puede entrar en ese foro.
- Con una o varias casillas, solo la ven los alumnos de esos lotes.
- Un usuario portal no ve el selector. Si envía ids en la petición, el servidor los ignora.
- El formulario de respuesta no muestra el selector.

## Configuración

El foro tiene que tener curso académico. Los lotes listados son los `op.batch` activos de ese curso. No hace falta marcarlos antes en el foro.

## Pruebas

```bash
docker run --rm --network odoo16irg_local_default \
  -v "$PWD/addons-extra:/mnt/extra-addons" \
  -v "$PWD/etc/odoo/odoo.local.conf:/etc/odoo/odoo.conf:ro" \
  odoo:16.0 \
  -c /etc/odoo/odoo.conf -d test_irg_web_post_batches \
  --stop-after-init --test-enable \
  --test-tags /irg_forum_web_post_batches --log-level=test
```

Resultado local: 8 tests, 0 failed, 0 errors.

## Limitaciones

- No se pueden elegir lotes al responder ni al editar el tema en la web. Eso sigue en la ficha de backend.
- Los administradores de sistema siguen viendo todas las publicaciones, como ya hacía la regla de visibilidad.
- El catálogo de lotes se lee con `sudo()` porque `op.batch` solo es legible por grupos de OpenEduCat. Los ids que se guardan siguen limitados a los lotes activos de ese curso.
