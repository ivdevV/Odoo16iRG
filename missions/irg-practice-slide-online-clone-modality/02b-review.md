# Review de código — irg-practice-slide-online-clone-modality

Alcance revisado (solo código funcional y tests):

- `addons-extra/extrairg/irg_practice_slide_restrictions/models/slide_slide.py`
- `addons-extra/extrairg/irg_practice_slide_restrictions/tests/test_practice_slide_restrictions.py`
- `addons-extra/extrairg/irg_practice_slide_restrictions/__manifest__.py`

Evidencia TDD consultada: RED con 1 fallo en `test_online_clone_allows_matching_modality_via_homeclass` (14 tests) y GREEN con 0 fallos y 0 errores (14 tests). Los dos tests de bloqueo del clon pasan ya en RED, lo que es coherente porque el comportamiento previo era fail-closed.

## Comprobación de criterios

| Criterio | Resultado |
| --- | --- |
| El clon resuelve cursos vía maestro | Cumple. `_irg_resolution_channel()` devuelve `irg_homeclass_channel_id` cuando existe. |
| Clon sin modalidad u otra modalidad queda oculto | Cumple. Cubierto por `test_online_clone_blocks_without_modality` y `test_online_clone_blocks_other_modality`. |
| Maestro sin regresión | Cumple. Un canal sin `irg_homeclass_channel_id` sigue el camino anterior; los tests previos siguen en GREEN. |
| Soft-check del campo | Cumple. `'irg_homeclass_channel_id' in channel._fields` es correcto porque el campo lo definen `irg_course_convocatorias(_v2)`, que no son dependencias del módulo; el helper de test hace `skipTest` si falta. |
| Fail-closed | Cumple. Sin canal devuelve recordset vacío, y cursos vacíos implica ninguna matrícula coincidente y `False`. |
| Seguridad server-side | Cumple. El `sudo()` solo se usa para leer la topología canal, asignatura y curso; la decisión sigue dependiendo de las matrículas del propio alumno. `slide_view` y `_get_slide_detail` del controlador reutilizan `_irg_courses_for_channel()`, así que el GET y la lista quedan alineados sin más cambios. |

Una autorreferencia (`base.irg_homeclass_channel_id = base`, que aparece en los tests de `irg_tfm_convocatorias`) es inocua: se resuelve con un único salto, sin recursión, y devuelve el mismo canal. El patrón coincide con el precedente que ya existe en `irg_course_elearning_featured_section/models/slide_channel.py` (`irg_get_featured_course`).

## Hallazgos

### MENOR — Se sustituye el canal del clon en vez de unirlo con el maestro

Archivo: `models/slide_slide.py`, en `_irg_resolution_channel` y `_irg_courses_for_channel`.

Cuando hay maestro, el canal del clon deja de consultarse por completo. Ahora mismo, si un clon estuviera vinculado directamente a un `op.course` mediante `op.course.slide_channel_ids` (campo de `isep_elearning_custom`), un alumno que antes estaba permitido pasaría a estar bloqueado. Es una regresión potencial, pero no es insegura porque solo puede ocultar contenido. El bug descrito indica que en producción los clones no tienen esa vinculación propia, y el precedente de featured section hace también la sustitución, así que no bloquea.

Sugerencia opcional: resolver los cursos como la unión de los de ambos canales (`self.channel_id | master`). Así se mantienen las dos fuentes y no se amplía el acceso más allá de los cursos legítimamente vinculados.

### NIT — Lógica de creación de canal duplicada en los tests

Archivo: `tests/test_practice_slide_restrictions.py`.

`_create_slide_channel` repite el bloque de la categoría Moodle y del patch de credenciales que ya contiene `_make_course_channel`. Se podría hacer que `_make_course_channel` reutilice el nuevo helper.

### NIT — El controlador no tiene test con un clon

Archivo: `tests/test_practice_slide_restrictions.py`.

No hay un test que ejerza `_get_slide_detail` o `slide_view` sobre un clon. El controlador delega en el mismo método ya cubierto, así que el riesgo es bajo.

### Manifest

El paso a `16.0.1.2.0` es correcto: hay cambio de comportamiento y no hay migración de datos ni campos nuevos.

## Veredicto

No hay hallazgos bloqueantes. El cambio es mínimo, está acotado al módulo, mantiene el comportamiento fail-closed y respeta la autorización en el servidor.

REVIEW OK
