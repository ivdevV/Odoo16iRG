# Modalidad de prácticas por matrícula y visibilidad eLearning

Fecha: 2026-09-02
Estado: aprobado para implementación en `feat/irg-practice-modality-elearning` (base `origin/Dev_iRG`)
Entorno: desarrollo hasta que el comportamiento sea estable. Sin push a `Dev_iRG` ni PR sin autorización nueva.

## Problema

El alumno elige un tipo de prácticas en la solicitud (`practice.request` → `practice.center.type`). Esa elección no queda en la matrícula (`op.student.course`) ni se usa para filtrar el campus. Un alumno con dos cursos necesita una modalidad por curso. El elearning de la asignatura de prácticas de cada curso debe mostrar secciones comunes a todos y secciones exclusivas de esa modalidad.

Esto no es la modalidad académica del máster (HomeClass / Online / Presencial, `irg_content_modality`).

## Decisiones cerradas

1. Fuente de verdad: campo en la matrícula, rellenado por la solicitud y corregible por staff.
2. Sin modalidad: solo se ven secciones sin requisito; las etiquetadas quedan bloqueadas.
3. Un cambio de modalidad (staff o nueva solicitud aprobada) cambia el campus al momento.
4. El filtro actúa por sección (categoría nativa de `slide.slide` / hijos).
5. Sección sin requisito = visible para todos. Sección con requisito = solo si coincide `type_of_practice`.
6. No hace falta marcar “es asignatura de prácticas”: cada curso ya tiene su canal de prácticas; staff etiqueta secciones en ese canal.
7. URL directa de contenido no autorizado: pantalla de aviso al estilo lotes/prerrequisitos, bloqueo en servidor.
8. Visible en ficha backend de la matrícula y, de forma informativa, en el campus junto a cada curso.
9. Si hay varias solicitudes del mismo curso, manda la última que esté en `approved`, `progress` o `end` (no solo `approved`, porque ese estado no es terminal).
10. Catálogo: todas las modalidades actuales de `practice.center.type.type_of_practice`. Prioridad de uso: másteres.

## Arquitectura: dos módulos nuevos

Ningún módulo existente se modifica. Prefijo `irg_`, ruta `addons-extra/extrairg/`.

### A — `irg_student_course_practice_modality`

Responsabilidad: persistir y mostrar la modalidad por matrícula.

- Campo `op.student.course.irg_practice_center_type_id` (Many2one `practice.center.type`, tracking).
- Al crear o escribir `practice.request`, si el estado está en `approved` / `progress` / `end`, se recopia en esa matrícula el tipo de la solicitud más reciente de ese grupo (`request_date desc, id desc`).
- Borrador, asignado o rechazado no copian ni borran el valor.
- Staff puede editar el campo en backend. Ese valor rige hasta que una solicitud posterior en estado de sync vuelva a copiar.
- `sudo()` solo para escribir el Many2one en la matrícula vinculada a `practice.request.course_id`. No se reescribe la solicitud.
- Superficies: formulario y árbol de `op.student.course`; línea informativa en el campus (`isep_website_custom.user_profile_content_details`) junto al nombre del curso; columna en la tabla educativa del portal OpenEduCat.
- Dependencias extra: `irg_practice_center_type_modalities` (claves `tfm_validation` / `on_site_origin`) y `openeducat_core_enterprise` (plantilla del portal educativo).

### B — `irg_practice_slide_restrictions`

Responsabilidad: requisito de visibilidad en slides. Depende de A.

- Campo `slide.slide.irg_required_practice_type`: Selection con las mismas claves que `practice.center.type.type_of_practice`. Vacío = común.
- `is_user_allowed_by_practice_type(user)`:
  - sin requisito efectivo → True;
  - público → False si hay requisito;
  - resuelve cursos del canal vía `op_subject_ids.course_id`, `op.course.subject_ids` y fallback `op.course.slide_channel_ids`;
  - busca la matrícula del alumno (`op.student` por `user_id`, si no por `partner_id`) cuyo `course_id` esté en esos cursos;
  - True solo si `enrollment.irg_practice_center_type_id.type_of_practice == requisito`.
- El requisito efectivo mira el propio slide, luego su categoría nativa y su padre. Un hijo dentro de una sección etiquetada queda restringido aunque su campo esté vacío (fail-closed). `inherit_limitations_from_parent` solo copia el valor al hijo cuando está vacío; no relaja el filtro de la sección.
- Si el alumno tiene dos matrículas, cada canal usa la de su curso. Si un canal compartido resuelve varios cursos, se admite si alguna matrícula coincide (limitación documentada).
- Controlador HTTP: la comprobación de prácticas va **antes** de `super().slide_view()` (lotes, fecha, prerrequisitos, morosidad). Si se delegara primero, `website_slides` entregaría el documento y llamaría a `action_set_viewed()`. Público con requisito → login; no autorizado → «Contenido Bloqueado».
- Índice y sidebar fullscreen ocultan secciones/slides no permitidos (no basta el CSS). Las plantillas heredan las de lote y unen condiciones con `and`.

Orden de instalación en dev: A, luego B.

## Seguridad

- La ocultación en QWeb no es autorización. El GET `/slides/slide/<id>` comprueba en servidor.
- `sudo()` se limita a leer matrícula, tipo y canal para decidir visibilidad, y a copiar el Many2one en el sync de A. El resultado no expone otros alumnos.
- El campo de matrícula es editable en backend por usuarios que ya pueden escribir `op.student.course`. El portal no ofrece selector; solo lectura.
- No hay secretos, borrado histórico ni cambio de autenticación de usuarios.

## Pruebas

Módulo A: campo presente; draft no sincroniza; `action_approve` / `progress` / `end` sí; la más reciente de esos estados gana; dos cursos independientes; rechazo no borra; staff puede escribir el campo; vistas heredadas contienen el campo.

Módulo B: vacío visible; sin modalidad + requisito bloquea; coincidencia permite; otra modalidad bloquea; dos cursos no se cruzan; hijo hereda requisito; plantilla de error se renderiza.

Validación Odoo: `docker-compose.local.yml` + overlay del worktree, base desechable, `-i` de ambos módulos, `--test-enable --test-tags`.

E2E TestSprite: obligatorio por alcance (plantillas portal y website_slides). `projectPath` = directorio del módulo B (superficie elearning). Credenciales solo de la base local. Prohibido beta/producción.

## Fuera de alcance

- Clonar canales por modalidad.
- Mezclar con `irg_content_modality` HomeClass/Online.
- Cambiar el formulario de solicitud de prácticas.
- Moodle.
- Un flag “es asignatura de prácticas” en `op.subject`.
- Commit, push o PR (autorizaciones separadas).
