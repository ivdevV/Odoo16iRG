# Execution — irg-business-api-academic-documents

## Base

- Branch: `Dev_iRG`
- HEAD: `df9c34d02dcee99b1741723769c79fb1bd78dd9a`

## Approach

Inline TDD. Review y Validación con subagentes distintos tras GREEN.

## RED

`2 failed, 2 error(s) of 71 tests`. El comando de notas aún aceptaba diploma/matrícula; los códigos nuevos no existían. Evidence: `artifacts/red-tests.txt`.

## GREEN

`0 failed, 0 error(s) of 71 tests` tras instalar `irg_generacion_diplomas` en la DB de prueba para cubrir diploma. Asistencia HC skipped (módulo no instalado). Evidence: `artifacts/green-tests.txt`.

## GREEN rework (bloqueante de review)

Tras REQUEST CHANGES: diploma exige `op.student.course.state == finished`;
no se restaura el gate de libreta `done` ni el pago del portal. Tests:
`test_diploma_rejects_running_course` + fixture `finished`. Apply de
matrícula/asistencia compara `admission_state`. Asistencia exige que
`session.batch_id` coincida con el de la admisión. Libreta interna: si el
lote no casa y hay varias candidatas, `UserError` (sin recencia). Preview
de diploma declara `course_state` y `will_create: irg.diploma.registry`.

`0 failed, 0 error(s) of 72 tests`. Evidence: `artifacts/green-rework.txt`.

## Review

Ronda 1: REQUEST CHANGES (diploma sin cierre académico). Ronda 2: REVIEW OK /
VERDICT APPROVE. Evidence: `02b-review.md`.

## Validation

PASS global. `0 failed, 0 error(s) of 72 tests`. Asistencia HC skipped
(`irg_certificate_attendance` no instalado). Diploma tests ejecutaron.
Evidence: `verification.json`, `03-validation.md`,
`artifacts/validation-tests.txt`.

## Documentation

Contrato, README, ficha de módulo, knowledge de notas + documentos académicos,
CHANGELOG de misión `16.0.1.4.0`. Sin cambios de código en esta fase.

## Publicación

No autorizada en esta conversación (ni commit ni push).
