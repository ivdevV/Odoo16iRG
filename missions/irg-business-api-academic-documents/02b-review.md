# Review de código — irg-business-api-academic-documents (ronda 2)

Revisor independiente (no es el codificador). Revisión de solo lectura: no se ha
editado código de producción ni se han ejecutado pruebas. El GREEN reportado por
el codificador (72 tests, 0 failed, 0 errors) se toma como dato de entrada, no se
reejecuta. Esta ronda reexamina el diff tras las correcciones al VERDICT
REQUEST CHANGES de la ronda 1.

## Alcance

Archivos funcionales de la misión:

- `addons-extra/extrairg/irg_business_api/models/document_service.py`
- `addons-extra/extrairg/irg_business_api/models/api_constants.py`
- `addons-extra/extrairg/irg_business_api/models/api_operation.py`
- `addons-extra/extrairg/irg_business_api/models/gradebook_service.py`
- `addons-extra/extrairg/irg_business_api/tests/test_academic_documents.py`
- `addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py`
- `addons-extra/extrairg/irg_business_api/tests/__init__.py`
- `addons-extra/extrairg/irg_business_api/__manifest__.py`

Contexto leído sin revisar como entregable: `00-spec.md`, `01-plan.md` y la
review previa de esta misma misión. Referencias auxiliares para contratos
externos: `irg.diploma.wizard`, `irg.diploma.registry`, `op.student.course.state`,
`irg.certificate.request` (create, origen, PDF),
`irg_certificate_attendance._validate_attendance_request` y
`irg_academic_request_history._check_academic_payment_eligibility`.

**No hay cambios en `irg_generacion_diplomas` ni en `irg_gradebook_certificates`.**
El alcance sigue acotado al módulo de la fachada.

## Criterios vs spec

| # | Criterio | Resultado | Evidencia |
| --- | --- | --- | --- |
| 1 | Tres códigos nuevos; el de notas se conserva | Cumple | `api_constants.py:73-76`. `irg_generate_gradebook_certificate` mantiene clave y etiqueta. |
| 2 | Diploma: `student_id` + `student_course_id` + `diploma_type` digital\|physical + `issue_date?`. Sin `gradebook_student_id` | Cumple | Allowlist `api_constants.py:167-175`. Validación `document_service.py:252-276`. Tests `test_academic_documents.py:165-166`, `:209`. |
| 3 | Diploma usa `irg.diploma.wizard.action_print_diploma` | Cumple | Apply `:313-314`. Preview declara `will_call` (`:286`) y `will_create: irg.diploma.registry` (`:287`). |
| 4 | Curso del diploma pertenece al alumno (control de servidor) | Cumple | `document_service.py:257-258`. El wizard oficial solo lo restringe por dominio de vista. |
| 5 | Curso `op.student.course.state == finished` | Cumple | `_diploma_vals` `:259-262`. Fixture `finished` (`test_academic_documents.py:48-50`). Test negativo `test_diploma_rejects_running_course` (`:171-190`). Preview expone `course_state` (`:167`, `:285`). Apply compara `course_state` (`:307-312`). |
| 6 | Diploma no exige libreta `done` ni pago de portal/máster | Cumple (decisión de producto) | La ruta no pasa por `irg.certificate.request` ni por `_check_academic_payment_eligibility`. La spec lo pide expresamente: «No usa libreta ni el pago del portal de certificados». No se exige reintroducir esos gates. |
| 7 | Matrícula: `admission_id` + opciones Word; libreta interna, no expuesta | Cumple | Allowlist sin `gradebook_student_id`. Resolución `_enrolment_record_for_admission` `:85-104`. Proposed y resultado no la incluyen. |
| 8 | Matrícula: `irg.certificate.request` `document_type=enrollment`, `origin=backend`, `state=done` | Cumple | `:106-119`. No dispara `_process_payment` (único origen de correo al alumno). |
| 9 | Asistencia: `admission_id` + `session_id` + mismas opciones Word; HC vía `new()` + `_validate_attendance_request` | Cumple | Preview `:193-219`, apply `:221-250`. Guarda por presencia de campo `session_id`, no por `ir.module.module`. |
| 10 | Notas: solo `gradebook` / `gradebook_partial`; diploma/enrollment/attendance → UserError con el comando nuevo | Cumple | `MOVED_DOCUMENT_TYPES` `gradebook_service.py:12-16`, `:106-109`. Tests de diploma y matrícula (`test_gradebook_certificate.py:184-200`). Asistencia está en el mapa; falta el test homólogo (MENOR). |
| 11 | Resultado: preview → approve, `file_b64`, checksum SHA-256, `public=False`, sin mail | Cumple | `_pdf_from_action` con `bin_size=False` y SHA-256. Abort si adjunto público. Ninguna ruta nueva llama a `_process_payment` ni `_send_*_notification`. Reserva: el «sin mail» de matrícula/asistencia no tiene test propio (MENOR). |
| 12 | Dispatch de escritura, savepoint de apply, sin PDF en preview | Cumple | `api_operation.py:298-300`, `:333-335`, savepoint `:399-412`. Tests `assertNotIn('file_b64', proposed)`. |
| 13 | Manifiesto `16.0.1.4.0`; sin dependencias duras nuevas | Cumple | `__manifest__.py:4`. Wizard y request se comprueban por presencia en `env`. |
| 14 | Sin cambios en módulos vetados | Cumple | Alcance anterior. |

Comprobaciones de arquitectura y seguridad que siguen en pie:

- Rebuild del payload en el apply desde `proposed_after` (readonly, escrito por el servidor) y revalidación completa. Sin atajos.
- Claves nuevas no coinciden con `SECRET_TOKENS`; `file_b64` sobrevive a `sanitize_mapping`.
- PDF por identidad (`/web/content/<id>`), no por recencia.
- Preview del diploma no consume secuencia ni crea `irg.diploma.registry`.
- El registro de diploma queda con `attachment_id` (ruta del wizard oficial).
- Sin `self.env.sudo()` nuevo ni flags de contexto; el `sudo` sigue siendo el del dispatch.
- `get_gradebook_summary` / `get_student_grade_evidence` no están en el diff.

## BLOQUEANTE anterior: estado

El único BLOQUEANTE de la ronda 1 era que `irg_generate_diploma` emitía un diploma
oficial numerado y verificable sin comprobar cierre académico, y que el suite lo
fijaba con un `op.student.course` `running`.

**Cerrado.** `_diploma_vals` rechaza `course.state != 'finished'` (el campo tiene
exactamente `running` \| `finished` en `openeducat_core/models/student.py:40-42`).
La fixture positiva usa `finished`. El test negativo
`test_diploma_rejects_running_course` restaura el estado en `finally`. El
`proposed` declara `course_state` y `will_create: irg.diploma.registry` (el número
de registro no puede anticiparse: la secuencia se consume en el apply). El apply
compara `course_state` contra `before`.

La parte del hallazgo anterior que pedía reintroducir libreta `done` y elegibilidad
de pago/máster **no es un defecto**. Contradice la spec aprobada y la decisión de
producto de esta misión. El diploma no debe pasar por el portal de certificados
ni por `irg.certificate.request`. No se reabre.

## Hallazgos

### BLOQUEANTE

Ninguno.

### MENOR

1. **La matrícula sigue sin exigir un estado de admisión válido.** El apply ahora
   compara `admission_state` (bloqueo optimista real, cierra el tautológico de la
   ronda 1 en ese punto), pero el preview acepta cualquier `op.admission`
   existente. Un certificado de matrícula sobre borrador o cancelada sigue siendo
   posible. `admission_state` está en `before` y no en `proposed`, que es lo que
   Lisa y el aprobador leen primero. Recomendación: conjunto explícito de estados
   y volcar `admission_state` al `proposed`.

2. **El cruce sesión/grupo de asistencia queda a medias.** Ahora se compara
   `session.batch_id` con `admission.batch_id`, pero solo si ambos están
   informados (`document_service.py:204`, `:237`). `op.admission.batch_id` no es
   `required` salvo en `submit` / `fees_paid`; si la admisión no tiene lote, el
   check no corre. Tampoco se compara contra el `batch_id` de la libreta
   realmente resuelta. El agujero principal (Lisa elige `session_id` de otro
   grupo cuando la admisión sí tiene lote) está cerrado. Falta el test del
   rechazo.

3. **Si el lote de la admisión no casa y hay exactamente una libreta, se usa en
   silencio.** Ya no se elige la más reciente entre varias: con más de una
   candidata se lanza `UserError` (`:95-103`). Con una sola libreta de otro lote
   se imprime ese grupo. Recomendación: fallar también cuando hay lote de
   admisión y cero coincidencias.

4. **Allowlists Word y extractor de PDF duplicados** entre `gradebook_service.py`
   y `document_service.py`. Sigue el riesgo de divergencia cuando se añada un
   firmante o un tipo.

5. **Huecos de cobertura.** No hay test de
   `document_type=attendance` en el comando de notas (el mapa sí redirige). No
   hay test del cruce sesión/lote, ni de varias libretas, ni de
   `student_course_id` ajeno al alumno, ni de `diploma_type` / `issue_date`
   inválidos, ni de «sin mail» en matrícula. Los tests de asistencia siguen
   dependiendo de que el módulo HC esté instalado en la DB de validación; el
   validador debe registrar ese `skipped` con justificación.

6. **`apply_generate_attendance` duplica el preview.** La revalidación es
   correcta; el copiar-pegar no. Extraer `_attendance_context(payload)`.

7. **La fecha del diploma no se fija en el preview** si el payload no trae
   `issue_date`. El humano aprueba sin ver la fecha; el apply resuelve
   `context_today` en otro momento.

8. **Nada impide varios diplomas `valid` para el mismo alumno y curso** con
   distinta `idempotency_key`. Debilidad compartida con el wizard oficial; aquí
   el agente reintenta más fácil. No es gate de spec.

9. **La deuda académica vencida de matrícula/asistencia se descubre en el apply**
   (`_check_academic_payment_eligibility` dentro de `_generate_and_attach_pdf`),
   después de la aprobación humana. El savepoint deshace el request. Limitación
   heredada del flujo Word oficial; el diploma, por decisión de producto, no
   pasa por ahí.

10. **Hallazgos heredados de retención** (`file_b64` indefinido en
    `result_snapshot`, `'public': False` literal en el dict de resultado, `.docx`
    temporal si el test solo parchea `_convert_to_pdf`, `target_model` apuntando
    al alumno/admisión y no al documento). No los introduce este diff.

### NIT

- Comparar `admission.id != before['admission_id']` (y el análogo de alumno/curso
  en diploma) sigue siendo tautológico una vez reconstruido el payload desde
  `proposed`. El valor de negocio ahora lo aporta `admission_state` /
  `course_state`.
- `_pdf_from_action` usa el mismo texto para URL, adjunto inexistente y PDF vacío.
- Tres `AcademicDocumentService(env)` por dispatch; una variable local bastaría.
- `state` en el resultado es el del request Word o el del `irg.diploma.registry`
  según el comando.
- `_admission` comprueba `'op.admission' not in self.env` con dependencia dura.
- Mensaje «Enrolment certificates are not installed.» también en asistencia.
- Wizard transitorio del preview de diploma sin comentario.
- `PDF_BYTES` / `PDF_CHECKSUM` duplicados en los dos archivos de test.
- `test_diploma_rejects_running_course` busca `'finished'` en el mensaje; una
  traducción futura rompería el assert. El msgid nuevo aún no está traducido, y
  el GREEN reportado es coherente.
- La nota de knowledge `irg_business_api_gradebook_certificate.md` sigue
  describiendo diploma como tipo del comando de notas con libreta `done`. Es
  trabajo de la fase Documentación, no un defecto de este código.

## Conclusión

La arquitectura de la spec se mantiene: tres comandos propios, diploma por el
wizard oficial de alumno y curso, matrícula y asistencia resolviendo la libreta
en servidor, comando de notas reducido a notas con redirección nominativa. El
BLOQUEANTE de la ronda 1 está cerrado con el gate `finished`, el test negativo y
la señal `will_create` / `course_state` en el preview. Las correcciones pedidas
sobre `admission_state`, cruce sesión/lote y resolución de libreta por recencia
están hechas en lo sustancial; quedan matices MENOR (admisión sin estado
exigido, check de lote que falla abierto si la admisión no tiene `batch_id`,
libreta única de otro lote). Ninguno es seguridad, pérdida de datos ni
incumplimiento de spec.

No hay hallazgos BLOQUEANTE. Los MENOR y NIT no bloquean Validación. La fase
Documentación deberá actualizar la nota de knowledge del comando de certificados.

VERDICT: APPROVE
REVIEW OK
