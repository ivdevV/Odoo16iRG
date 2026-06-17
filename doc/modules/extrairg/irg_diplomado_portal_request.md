# irg_diplomado_portal_request

## Proposito

Modulo Odoo 16 para solicitar desde el portal del alumno el diploma especifico de un diplomado. El flujo queda separado del portal general de certificados y diplomas de masteres.

## Comportamiento funcional

- Anade un tile especifico `Diploma del Diplomado` en las herramientas del curso cuando el curso es un diplomado.
- Oculta el tile generico `Certificados y Diplomas` en cursos de diplomado.
- Permite descargar el diploma solo si la libreta academica del alumno esta completada y la calificacion final es estrictamente superior a `7.0`.
- Al pulsar `Descargar Diploma`, crea el registro `irg.diplomado.registry` si todavia no existe, genera el PDF y responde con la descarga directa.
- Vincula automaticamente una solicitud pendiente cuando secretaria emite un registro en `irg.diplomado.registry`.
- Permite descargar el PDF emitido solo al alumno propietario y solo si mantiene la nota final requerida.

## Rutas portal

| Ruta | Metodo | Uso |
| --- | --- | --- |
| `/campus/diplomados/<course_id>` | `GET` | Pagina contextual del diplomado |
| `/campus/diplomados/<course_id>/request` | `POST` | Genera/recupera el diploma y descarga el PDF si cumple requisitos |
| `/campus/diplomados/download/<registry_id>` | `GET` | Descarga segura del PDF emitido |

## Modelos

### `irg.diplomado.portal.request`

Modelo historico interno del modulo para compatibilidad administrativa. El flujo portal actual no deja solicitudes pendientes: descarga directamente el diploma si cumple requisitos.

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
- Si no existe diploma emitido para el alumno y curso, el portal lo crea automaticamente antes de descargarlo.
- Si ya existe, reutiliza el registro emitido y descarga su PDF.

## Validacion

Validado en Odoo local con `docker-compose.local.yml`:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_diplomado_portal_request --test-enable --test-tags /irg_diplomado_portal_request --stop-after-init --http-port=8099 --log-level=test
```

Resultado: `0 failed, 0 error(s)`.

La correccion de descarga directa se valido con el mismo comando. El test comprueba que el `POST` devuelve el binario PDF y que no se crea una solicitud pendiente.

Tambien se validaron compilacion Python y parseo XML del modulo.

## Limitaciones conocidas

- La pagina de curso del portal depende del contexto de perfil de la instalacion. Por eso el test del tile valida la vista heredada QWeb directamente, mientras que el flujo funcional se valida mediante rutas portal dedicadas.
- La descarga usa `http.send_file`, consistente con modulos existentes del proyecto, aunque Odoo 16 muestra aviso de deprecacion recomendando `http.Stream`.
