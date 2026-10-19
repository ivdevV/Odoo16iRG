# Plan — irg-student-activity

## Objetivo

En la ficha de alumno (`op.student`), pestaña **Actividad** (tras Acceso) con
historial cronológico de campus + evaluaciones y botón **Exportar CSV** para
Facultad. Acceso no se modifica.

Diseño aprobado: `docs/superpowers/specs/2026-10-15-irg-student-activity-design.md`.

Plan de implementación: `docs/superpowers/plans/2026-10-15-irg-student-activity.md`.

Módulo nuevo: `addons-extra/extrairg/irg_student_activity` (`16.0.1.0.0`).
Dependencias: `openeducat_core`, `isep_student_access`, `isep_elearning_custom`,
`website_slides_survey`.

## Clasificación

- Clase: `full`.
- Tier: `standard` (módulo nuevo acotado, UI, lectura cross-model, export; sin
  auth/migraciones/secretos).
- Jev intake: `skipped` (`http_error`). `effective_class_binding` es falso.
  La clase la fija esta política.
- Security Advisor: no forzado. El diseño ya exige `has_group` server-side.

## jev_intake

```json
{
  "status": "skipped",
  "skipped_reason": "http_error",
  "model": null,
  "mission_class": null,
  "mission_class_confidence": null,
  "mission_class_binding": false,
  "exceeds_simple_limits": false,
  "exceeds_simple_noul": null,
  "needs_security_advisor": false,
  "security_noul": null,
  "security_keyword_hit": false,
  "effective_class": null,
  "effective_class_binding": false
}
```

## E2E

Obligatorio: el diff toca vistas XML del formulario de alumno.
`projectPath` = `addons-extra/extrairg/irg_student_activity`.
Runtime `docker-compose.local.yml` puerto 8069, DB desechable.

## Criterios de aceptación

1. Pestaña Actividad con historial campus + evaluaciones (orden desc, máx. 500).
2. Acceso sin cambios de comportamiento.
3. Export CSV con las mismas columnas/filas.
4. Sin grupo Facultad → `AccessError` en servidor.
5. Tests de módulo en verde y E2E PASS.
