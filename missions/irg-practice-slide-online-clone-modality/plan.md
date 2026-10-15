# Mission Plan — irg-practice-slide-online-clone-modality

## Fuente y objetivo

- Diagnóstico (sesión): en clones online (`slide.channel` 319/329/331 con `irg_homeclass_channel_id`), `_irg_courses_for_channel()` no resuelve cursos porque `op_subject_ids` vive en el maestro. Secciones con `irg_required_practice_type` quedan ocultas aunque la matrícula tenga modalidad.
- Objetivo: que el filtro resuelva cursos vía el canal maestro cuando el canal visto es un clon online, y muestre secciones cuya modalidad coincida con la matrícula.
- Sin dar acceso al canal HomeClass (127); sin dos accesos a Prácticas.

## Knowledge

- `irg_practice_modality_elearning.md`: resolución curso↔canal por `op_subject_ids` ∪ `subject_ids` ∪ `slide_channel_ids`; vacío = común.
- `irg_elearning_online_clone_resolution.md`: clon apunta a maestro con `irg_homeclass_channel_id`; no inventar enlaces por nombre.
- `doc/modules/extrairg/irg_practice_slide_restrictions.md`: documentación del módulo a actualizar.

## jev_intake

```json
{"status": "skipped", "skipped_reason": "http_error", "model": null, "mission_class": null, "mission_class_confidence": null, "mission_class_binding": false, "exceeds_simple_limits": false, "exceeds_simple_noul": null, "needs_security_advisor": false, "security_noul": null, "security_keyword_hit": false, "effective_class": null, "effective_class_binding": false}
```

Clasificación orquestador (Jev skipped): **misión `full`**, bugfix de comportamiento de producto. No fuerza Security Advisor.

## Clasificación

- **Tier:** `standard` — lógica acotada en 1–2 archivos de producción + tests; soft-check de campo existente.
- Capacidad: razonamiento alto de esta sesión. Sin selector de modelo.

## Roles

Plan (orquestador) → Implementación/TDD (codificador) → Review (distinto) → Validación → Documentación → Publicación solo con OK.

## Alcance

### Archivos

| Archivo | Cambio |
| --- | --- |
| `addons-extra/extrairg/irg_practice_slide_restrictions/models/slide_slide.py` | Resolver canal efectivo (maestro si clon) en `_irg_courses_for_channel` |
| `addons-extra/extrairg/irg_practice_slide_restrictions/tests/test_practice_slide_restrictions.py` | Tests RED/GREEN: clon sin `op_subject_ids`, maestro con asignatura |
| `addons-extra/extrairg/irg_practice_slide_restrictions/__manifest__.py` | Bump patch version |
| `doc/modules/extrairg/irg_practice_slide_restrictions.md` | Documentar resolución vía maestro |
| `.agents/knowledge/.../irg_practice_modality_elearning.md` | Gotcha de clones online |

### No alcance

- No enlazar lotes en el clon ni rellenar `irg_online_batch_ids`.
- No dar membership al canal 127.
- No etiquetar 6616/6617 (aparte informado; fuera de esta misión).
- No nuevo addon: el soft-check de `irg_homeclass_channel_id` evita dependencia dura de convocatorias.

## Diseño

En `_irg_courses_for_channel`, si el canal tiene `irg_homeclass_channel_id` y apunta a un maestro, usar ese maestro (sudo) como fuente de `op_subject_ids` / `slide_channel_ids`. Si el campo no existe o está vacío, comportamiento actual.

## Criterios de aceptación

1. Sección con `irg_required_practice_type` en un canal clon (sin asignaturas propias) es visible si la matrícula del alumno en el curso del maestro tiene esa modalidad.
2. Misma sección permanece oculta si la matrícula no tiene modalidad o tiene otra.
3. Canal maestro sin cambio de comportamiento.
4. Tests del módulo en verde en base desechable vía `docker-compose.local.yml`.

## E2E

Disparo **no**: el diff toca solo Python de modelo/tests/docs; no vistas ni QWeb nuevos. Check `e2e_testsprite` → `skipped` justificado por scope.

## Seguridad

No autenticación nueva, migraciones, secretos ni borrado. Soft-check de campo. Fail-closed si no hay matrícula coincidente se mantiene.

## Restricciones

- No commit/push/PR sin OK explícito nuevo.
- Tests: `docker compose -f docker-compose.local.yml run --rm --no-deps`; no dejar el servicio compartido montado a worktree.
- Runtime: `docker-compose.local.yml`.
