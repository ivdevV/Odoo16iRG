# Mission Plan — irg-practice-modality-elearning

## Fuente y objetivo

- Spec: `docs/superpowers/specs/2026-09-02-practice-modality-elearning-design.md`
- Plan detallado: `docs/superpowers/plans/2026-09-02-practice-modality-elearning.md`
- Objetivo: dos módulos nuevos. A guarda la modalidad de prácticas en `op.student.course`. B filtra secciones de elearning con esa variable.
- Base: rama `feat/irg-practice-modality-elearning` desde `origin/Dev_iRG` (`cf0e8fd7e`).
- Worktree: `.worktrees/irg-practice-modality-elearning`

## Knowledge

- `modding_rules_and_email_analysis.md`: addon nuevo en `addons-extra/extrairg/`, prefijo `irg_`, herencia, sin editar existentes.
- `irg_course_elearning_featured_section.md`: resolver curso desde `op.subject.slide_channel_id` / `op_subject_ids`, no hay `course_id` fiable en `slide.channel`.
- Patrón de visibilidad: `irg_batch_slide_restrictions` (vacío = todos; GET bloquea; QWeb oculta).

## Clasificación

- **Tier:** `complex` — más de cinco archivos, cross-module (prácticas + matrícula + elearning), control de acceso a contenido.
- **Misión:** `full`
- Capacidad: razonamiento alto. No hay selector de modelo en este runtime; se documenta la capacidad usada.

## Roles

1. Plan — orquestador (esta sesión).
2. Implementación/TDD — codificador.
3. Review — distinto del codificador.
4. Validación — independiente; `verification.json`.
5. Documentación — tras review y validación passed.
6. Publicación — no aplica hasta autorización de commit/push/PR.

## E2E

Disparo **sí**: el diff toca QWeb de portal y `website_slides`. Check `e2e_testsprite` después del resto en verde. `projectPath` = `addons-extra/extrairg/irg_practice_slide_restrictions`.

## Seguridad

No es autenticación de usuarios, migración destructiva ni secretos. Sí es acción protegida (ver documento). Control server-side obligatorio.

`[YES] Reason: visibility is enforced on the slide GET; sudo is limited to syncing the enrollment Many2one and reading the current student's course modality; no historical deletion or secrets.`

## Criterios de aceptación

- Matrícula tiene modalidad; solicitud draft no la escribe; `approved`/`progress`/`end` sí; la más reciente de esas gana; dos cursos independientes.
- Staff edita el campo y el campus lo usa al momento.
- Sección sin requisito visible; con requisito solo si coincide `type_of_practice`.
- Sin modalidad, las etiquetadas bloquean con aviso.
- URL directa no entrega el documento.
- Cero cambios en módulos preexistentes.
- Tests A y B verdes en compose local + overlay.
- `verification.json` `passed`.

## Restricciones de entrega

- No commit, push ni PR sin OK explícito nuevo.
- No tocar el checkout principal sucio.
- Restaurar el servicio Docker para que no quede montado el worktree.
