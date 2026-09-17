# Code Review — irg-practice-modality-elearning (ronda 2)

Revisor independiente del codificador. Solo lectura: no se ejecutaron tests ni se
editó código de producción.

- Rama: `feat/irg-practice-modality-elearning`
- Worktree: `.worktrees/irg-practice-modality-elearning`
- Alcance revisado: `addons-extra/extrairg/irg_student_course_practice_modality/`
  y `addons-extra/extrairg/irg_practice_slide_restrictions/` (modelos, tests,
  vistas/QWeb, controlador, manifests, `__init__`).
- Fuera de alcance por política: `plan.md`, `execution.md`, `verification.json`,
  changelog y documentación como calidad editorial.
- Objeto de esta ronda: verificar que los dos BLOQUEANTES de la ronda 1 están
  realmente cerrados y que las correcciones no introdujeron regresiones nuevas.

## Estado de los hallazgos de la ronda 1

| Ref ronda 1 | Estado | Comprobación |
| --- | --- | --- |
| BLOQUEANTE-1 — onchange sin decorador | **Cerrado** | `slide_slide.py:93` lleva `@api.onchange('parent_slide_id', 'inherit_limitations_from_parent')`, exactamente los mismos disparadores que `irg_elearning_editable_sections/models/slide_slide.py:35`. Hay test de regresión que exige la presencia del método en `_onchange_methods['parent_slide_id']` y que `allowed_batch_ids` del padre siga propagándose. |
| BLOQUEANTE-2 — fixture atado a `odoo_moodle_connector` | **Cerrado** | `test_practice_slide_restrictions.py:53-74`: `category_id` solo se rellena si el campo existe y `'moodle.categories' in self.env`; el `patch` va en `ExitStack` con `except (ImportError, AttributeError)`. `ModuleNotFoundError` hereda de `ImportError`, y si `__enter__` lanza, `ExitStack` no registra el exit, así que la pila no queda corrupta. El bloque muerto duplicado desapareció. |
| MENOR-1 — `_irg_courses_for_channel` incompleto | **Cerrado** | `slide_slide.py:52-55` añade `subjects.mapped('course_id')` y queda alineado con el patrón de `irg_course_convocatorias_v2/models/slide_channel.py:199-203`. Cubierto por `test_allows_when_course_linked_only_via_subject_course_id`, que es un test válido porque `op.course.subject_ids` es Many2many y no es el inverso de `op.subject.course_id`. |
| MENOR-2 — N+1 en `_get_slide_detail` | **Cerrado** | `controllers/main.py:38-46` resuelve alumno y cursos una sola vez y los inyecta en cada llamada. |
| MENOR-3 — QWeb con requisito crudo | **Cerrado** | Las dos guardas de sección usan `irg_has_practice_requirement()`, que delega en `_irg_effective_practice_type()`. La tercera plantilla usa `practice_blocked_slide_ids`, que ya se calcula con el requisito efectivo. |
| MENOR-4 — herencia sin mirar `inherit_limitations_from_parent` | **Aceptado y documentado** | El `help` del campo (`slide_slide.py:12-17`) declara el fail-closed. Ver MENOR-1 de esta ronda: falta alinear la spec. |
| MENOR-5 — orden en el controlador | **Aceptado con motivo** | Se mantiene el bloqueo antes de `super()`. El motivo es sólido: `website_slides.slide_view` ejecuta `action_set_viewed()`, así que comprobar después registraría visualización de contenido bloqueado. Ver MENOR-2 de esta ronda. |
| MENOR-6 — `_apply_parent_limitations` sin guarda | **Cerrado** | `slide_slide.py:110-111`. La guarda va después del `super()`, que es lo correcto: el hook de `irg_elearning_editable_sections` nunca tuvo guarda propia y este módulo no debe cambiar su comportamiento. |
| NIT `Subject.browse()` | Cerrado (`slide_slide.py:43,50`) |
| NIT `filtered(lambda rec: rec)` | Cerrado (`practice_request.py:29`) |
| NIT `contains(@class, ...)` | Persiste; es el `expr` de la vista padre, no se toca |
| NIT deps extra del manifest A | Persiste; pendiente de Documentación |
| NIT `irg_get_practice_center_type` público | Persiste; sin impacto |

## Verificación de los criterios de producto

| # | Criterio | Resultado |
| --- | --- | --- |
| 1 | Fuente de verdad en `op.student.course.irg_practice_center_type_id`, sync desde la última `practice.request` en `approved`/`progress`/`end` con `request_date desc, id desc`; draft/assigned/rejected no copian ni borran | Cumple |
| 2 | Staff escribe el campo; el campus usa el valor al momento | Cumple |
| 3 | Sección sin requisito visible; con requisito solo si coincide `type_of_practice` | Cumple |
| 4 | Sin modalidad las etiquetadas bloquean; el GET `/slides/slide/<id>` bloquea en servidor; misma familia de aviso «Contenido Bloqueado» | Cumple |
| 5 | El QWeb de listas conserva las condiciones de lote al añadir las de prácticas | Cumple |
| 6 | Cero cambios en módulos preexistentes | Cumple, también en comportamiento |
| 7 | `sudo()` solo para el sync del Many2one y las lecturas de visibilidad del alumno actual | Cumple |

Comprobaciones que respaldan la tabla:

- El criterio 6 era el que estaba roto en la ronda 1. Con el decorador restaurado,
  `_onchange_methods` vuelve a resolver el método y la cadena `super()` ejecuta
  primero la propagación de `category_id`, `allowed_batch_ids` y `scheduled_date`
  de `irg_elearning_editable_sections`. La no-regresión está blindada por
  aserción explícita sobre `allowed_batch_ids`, no solo por el campo nuevo.
- Las guardas de `course_slides_list` y del sidebar de secciones reproducen
  literalmente la condición de lote del padre y la combinan con `and`, con el
  paréntesis correcto: `not category[...] or ((lote) and (prácticas))`. No hay
  precedencia mal puesta que abra una sección bloqueada por lote.
- El `t-if` convive con `t-foreach` en el mismo nodo, que es el patrón ya
  existente: QWeb evalúa `foreach` antes que `if`, así que la condición se
  evalúa por iteración con `category` ya asignado.
- La cadena de controladores es
  `WebsiteSlidesPracticeRestrictions → WebsiteSlidesBatchRestrictions →
  WebsiteSlidesCustom → website_slides`. Todas las capas siguen ejecutándose
  porque cada eslabón delega en `super()`.
- `op.student.course` hereda `mail.thread` (`openeducat_core/models/student.py:29`),
  así que el `tracking=True` del campo nuevo es efectivo y no ruido.
- Los `__init__.py` no importan `tests`, el manifest no lo declara y no hay
  modelos nuevos, de modo que no falta `ir.model.access.csv`.

## Hallazgos de esta ronda

### BLOQUEANTE

Ninguno.

### MENOR-1 — La spec sigue describiendo una herencia que el código no implementa

**Archivo:** `docs/superpowers/specs/2026-09-02-practice-modality-elearning-design.md:53`

La spec dice «Los hijos con `inherit_limitations_from_parent` copian el requisito
del padre cuando el hijo está vacío». El código es más restrictivo a propósito:
`_irg_effective_practice_type()` hereda de `category_id` y `parent_slide_id` sin
mirar el flag, y el `help` del campo ya lo documenta como fail-closed. La decisión
es defendible y falla en cerrado, pero mientras la spec diga otra cosa hay dos
contratos escritos y contradictorios sobre el mismo comportamiento.

No bloquea porque no afecta a seguridad ni a la arquitectura y el comportamiento
efectivo es el más seguro de los dos.

**Corrección:** en Documentación, actualizar esa línea de la spec para que
describa el fail-closed por sección y deje el flag como «copia el valor al hijo»,
no como condición de la restricción.

### MENOR-2 — La spec sigue describiendo un orden de comprobación distinto al real

**Archivo:** `docs/superpowers/specs/2026-09-02-practice-modality-elearning-design.md:54`

La spec dice «Controlador HTTP, después de lotes/prerrequisitos» y el controlador
comprueba prácticas antes de `super()`. El motivo registrado es correcto y no lo
discuto: `website_slides.slide_view` marca la slide como vista, así que comprobar
después dejaría rastro de visualización de contenido bloqueado. El efecto lateral
aceptado es que un alumno bloqueado a la vez por morosidad y por modalidad verá el
aviso de modalidad.

**Corrección:** en Documentación, cambiar la spec para que refleje el orden real y
su motivo. No tocar el controlador.

### MENOR-3 — `is_user_allowed_by_practice_type` expone parámetros de autorización precalculados

**Archivo:** `addons-extra/extrairg/irg_practice_slide_restrictions/models/slide_slide.py:70`

La firma pública pasó a ser
`is_user_allowed_by_practice_type(self, user, student=None, courses=None)`. Es un
método público y por tanto invocable por RPC con valores arbitrarios en los tres
argumentos.

He verificado que hoy **no** hay bypass: el gate real (`slide_view:25`) y el QWeb
llaman siempre sin sobrescribir `student` ni `courses`; por RPC un `user` entero
revienta en `_is_public()`, un `student` entero revienta en `course_detail_ids`, y
un `courses` como lista de enteros hace que `rec.course_id in courses` sea siempre
falso, es decir, falla en cerrado. Y en cualquier caso el retorno es un booleano,
no una concesión de acceso. Por eso es MENOR y no BLOQUEANTE.

Aun así, un método público cuyo resultado de autorización depende de entradas del
llamante es un foot-gun: basta que un futuro controlador reenvíe algo del request
para convertirlo en un agujero.

**Corrección:** mover el cuerpo a un `_irg_is_allowed_by_practice_type(user,
student, courses)` privado y dejar `is_user_allowed_by_practice_type(self, user)`
como envoltorio de un solo argumento, que es la firma que consumen QWeb y el
controlador. `_get_slide_detail` llamaría al privado.

## NIT

- `controllers/main.py:38-41`: el alumno y los cursos se resuelven llamando a los
  helpers sobre `channel_slides[:1]` en vez de sobre `slide`, que ya está en la
  mano y siempre pertenece al mismo canal. Funciona, pero obliga a razonar sobre
  el caso de canal vacío para nada. `slide._irg_student_for_user(user)` y
  `slide._irg_courses_for_channel()` serían directos.
- `controllers/main.py:37`: se itera `channel_id.slide_ids`, mientras la capa de
  lotes itera `slide_content_ids`. Es un superconjunto inocuo (mete categorías en
  el set), pero conviene igualar el criterio con la capa que hereda la plantilla.
- `slide_slide.py:35` y `:70`: ambos métodos son públicos y usan `sudo()` por
  dentro, así que por RPC se puede sondear si una slide tiene requisito. La
  información filtrada es un booleano sobre la taxonomía del contenido; sin
  impacto práctico.
- `__manifest__.py` (módulo A): `irg_practice_center_type_modalities` y
  `openeducat_core_enterprise` siguen sin quedar justificadas en documentación.
  Ambas están bien puestas (claves del catálogo y plantilla
  `student_portal_educational_information`), es solo trazabilidad.
- `templates.xml:24`: el `contains(@class, ...)` sigue generando el warning
  «Error-prone use of @class» al arrancar. Es el precio de replicar el `expr` de
  la vista padre.

## Seguridad

Sin hallazgos bloqueantes.

- El control de acceso vive en el servidor (`slide_view`), no en el QWeb, como
  exige `AGENTS.md`. La ocultación en índice y sidebar es defensa cosmética
  añadida, no el control.
- Revisado el vector de escalada del sync de A: `ir.model.access.csv` de
  `isep_practices_2` concede `practice.request` a `base.group_user`, no al portal,
  y los controladores de portal que crean solicitudes con `sudo()`
  (`irg_practice_center_restrict`, `irg_practice_request_student_profile`,
  `isep_practices_2/my_practices_request_new`) construyen el `values` con claves
  explícitas y no aceptan `state` desde el formulario, de modo que la solicitud
  nace en `draft`. Un alumno no puede fabricar una solicitud `approved` y
  autoasignarse una modalidad para desbloquear contenido.
- `sudo()` acotado: en A a buscar las solicitudes de esa matrícula y escribir el
  Many2one; en B a leer canal, cursos, el `op.student` del usuario en curso y su
  matrícula. No se leen ni exponen datos de otros alumnos.
- La plantilla del campus resuelve
  `env['op.student'].sudo().search([('user_id','=',user.id)])`, y
  `isep_website_custom.user_profile_content_details` solo se renderiza desde
  `user_profile_course`, cuyo controlador fija `user_id = request.env.user.id`.
  No hay fuga cruzada de perfiles.
- Sin modelos nuevos, sin secretos, sin migraciones ni borrado histórico. El campo
  de matrícula solo es escribible por quien ya puede escribir `op.student.course`;
  el portal es de solo lectura.

REVIEW OK
