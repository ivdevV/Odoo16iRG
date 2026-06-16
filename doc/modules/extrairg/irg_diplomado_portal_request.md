# irg_diplomado_portal_request

## Proposito

Modulo Odoo 16 para solicitar desde el portal del alumno el diploma especifico de un diplomado. El flujo queda separado del portal general de certificados y diplomas de masteres.

## Comportamiento funcional

- Anade un tile especifico `Diploma del Diplomado` en las herramientas del curso cuando el curso es un diplomado.
- Oculta el tile generico `Certificados y Diplomas` en cursos de diplomado.
- Permite solicitar el diploma solo si la libreta academica del alumno esta completada y la calificacion final es estrictamente superior a `7.0`.
- Registra solicitudes en el modelo propio `irg.diplomado.portal.request`.
- Vincula automaticamente una solicitud pendiente cuando secretaria emite un registro en `irg.diplomado.registry`.
- Permite descargar el PDF emitido solo al alumno propietario y solo si mantiene la nota final requerida.

## Rutas portal

| Ruta | Metodo | Uso |
| --- | --- | --- |
| `/campus/diplomados/<course_id>` | `GET` | Pagina contextual del diplomado |
| `/campus/diplomados/<course_id>/request` | `POST` | Crea la solicitud si cumple requisitos |
| `/campus/diplomados/download/<registry_id>` | `GET` | Descarga segura del PDF emitido |

## Modelos

### `irg.diplomado.portal.request`

Campos principales:

- `student_id`: alumno solicitante.
- `course_id`: diplomado solicitado.
- `gradebook_student_id`: libreta academica usada como evidencia.
- `final_grade`: nota final en el momento de solicitud.
- `state`: `requested`, `processed` o `cancelled`.
- `diplomado_registry_id`: diploma emitido vinculado.

### Extension de `op.course`

El helper `irg_is_diplomado()` identifica diplomados por codigo de curso, tipo de curso y productos/categorias relacionadas.

### Extension de `irg.diplomado.registry`

Al crear o cambiar un registro emitido, el modulo busca una solicitud `requested` del mismo alumno y curso y la marca como `processed`.

## Reglas academicas

- El curso debe ser diplomado.
- La libreta debe estar en estado `done`.
- La nota final debe ser `> 7.0`.
- La solicitud no se crea si ya existe un diploma emitido o una solicitud activa para el mismo alumno y curso.

## Validacion

Validado en Odoo local con `docker-compose.local.yml`:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_diplomado_portal_request --test-enable --test-tags /irg_diplomado_portal_request --stop-after-init --http-port=8099 --log-level=test
```

Resultado: `0 failed, 0 error(s)`.

Tambien se validaron compilacion Python y parseo XML del modulo.

## Limitaciones conocidas

- La pagina de curso del portal depende del contexto de perfil de la instalacion. Por eso el test del tile valida la vista heredada QWeb directamente, mientras que el flujo funcional se valida mediante rutas portal dedicadas.
- La descarga usa `http.send_file`, consistente con modulos existentes del proyecto, aunque Odoo 16 muestra aviso de deprecacion recomendando `http.Stream`.
