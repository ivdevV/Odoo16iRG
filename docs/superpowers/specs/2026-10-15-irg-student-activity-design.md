# Actividad del alumno en el expediente

## Problema

El departamento académico necesita ver en la ficha del alumno (`op.student`) qué ha hecho en el campus: contenidos e-learning y evaluaciones, en orden cronológico. La pestaña **Acceso** solo muestra logins (`op.login.lines`) y credenciales; no debe mezclarse con actividad académica.

Ya existe `irg_campus_activity_audit`: informe Excel por lote con las mismas fuentes (campus, evaluaciones, libreta). No ofrece historial por alumno en el expediente ni export CSV desde la ficha.

El módulo OCA `auditlog` no aplica: registra create/write/delete ORM, no el progreso de campus ni intentos de encuesta.

## Alcance (v1)

Módulo nuevo `irg_student_activity` en `addons-extra/extrairg/`. Extiende `op.student` por herencia de vista/modelo. No modifica `isep_student_access` ni la pestaña Acceso.

Dependencias previstas: `openeducat_core`, el puente e-learning que aporte `slide_id` en `survey.user_input` (p. ej. `isep_elearning_custom` / stack slides+survey ya usado por el informe de lote). Confirmar en el plan frente a manifests instalados.

**Incluido**
- Pestaña **Actividad** en el formulario de `op.student` (después de Acceso).
- Historial cronológico de solo lectura: eventos de campus (`slide.slide.partner`) + evaluaciones (`survey.user_input`).
- Botón **Exportar CSV** con las mismas columnas y filas visibles (máx. 500 eventos más recientes).
- Autorización server-side para Facultad; lectura con `sudo()` solo lectura tras el check.

**Fuera de alcance en v1**
- Ampliar columnas de Acceso / mezclar logins.
- Libreta, Moodle, foros, asistencia, tareas `op.assignment`.
- Import de listados o de eventos externos.
- Tabla persistente de eventos / clickstream fino (cada visita).
- Portal del alumno.
- Cambiar el Excel por lote de `irg_campus_activity_audit` (sigue existiendo para análisis masivo).

## Relación con el informe de lote

| | Ficha alumno (este módulo) | Informe lote (`irg_campus_activity_audit`) |
| --- | --- | --- |
| Unidad | Un `op.student` | Un `op.batch` (+ listado opcional) |
| Vista | Timeline cronológica | Excel multi-hoja |
| Fuentes v1 | Campus + evaluaciones | Campus + evaluaciones + libreta + flags |
| Export | CSV | XLSX |

Comparten fuentes de lectura y el mismo grupo Facultad. No es obligatorio depender del addon del informe; se puede factorizar lectura común en una fase posterior si conviene. En v1 se acepta lógica de ensamblado propia en `irg_student_activity` alineada con las reglas del informe (sin libreta).

## Flujo

1. Usuario interno con `openeducat_core.group_op_faculty` abre un `op.student`.
2. Abre la pestaña **Actividad**.
3. El sistema ensambla al vuelo los eventos del `partner_id` del alumno (campus + evaluaciones), ordenados por fecha descendente, hasta 500.
4. Opcionalmente pulsa **Exportar CSV** y descarga un adjunto temporal no público.
5. No escribe progreso, matrículas, canales ni logs de auditoría.

## UI

Pestaña `Actividad` en `view_op_student_form` (xpath tras `page[@name='access']` si existe; si no, tras información personal / posición estable documentada en implementación).

Columnas de la tree readonly:

| Columna | Contenido |
| --- | --- |
| Fecha | Timestamp del evento |
| Tipo | `Campus` / `Evaluación` |
| Curso / canal | Nombre del canal e-learning |
| Elemento | Nombre del contenido o de la evaluación (slide) |
| Detalle | Campus: En curso / Completada · Evaluación: estado del intento |
| Resultado | Campus: vacío si En curso; `Completada` si `completed` · Evaluación: porcentaje (`scoring_percentage`) y/o éxito (`scoring_success`) si existen |
| Lote | Código de lote si se resuelve; si no, vacío |

Reglas de filas:
- Campus: solo filas con `slide.slide.partner` existente (progreso real). No listar “No iniciada”.
- Evaluación: cada `survey.user_input` del partner con `slide_id` (si el campo existe en el modelo).
- Sin paginación custom: tree estándar Odoo + límite 500 en el ensamblado.

CSV: mismas columnas + cabecera; nombre `actividad_<slug_alumno>_<YYYYMMDD>.csv`. Si el alumno tiene más de 500 eventos, el export incluye solo esos 500 más recientes (comportamiento documentado; no segundo archivo).

## Datos y fechas

**Campus**
- Origen: `slide.slide.partner` del `partner_id` del alumno, slide publicado y no sección (misma noción de contenido que el informe de lote).
- Fecha: `write_date` del `slide.slide.partner`; si faltara, `create_date`.
- Detalle: Completada si `completed`; si no, En curso.

**Evaluación**
- Origen: `survey.user_input` con `partner_id` del alumno y `slide_id` informado.
- Fecha: `end_datetime` si el campo existe y está relleno; si no, `create_date`.
- Detalle / Resultado: `state`, `scoring_percentage`, `scoring_success` cuando existan.

**Lote**
- Best-effort: via `slide.channel.partner` / matrícula del alumno ligada al canal. Si no hay resolución fiable, columna vacía.

**Ensamblado**
- Servicio interno del módulo que produce filas homogéneas.
- Presentación en UI mediante modelo transient o mecanismo computed no persistente (detalle de implementación en el plan; requisito: no crear tabla histórica de eventos).
- Export: mismo ensamblado → CSV → attachment temporal / descarga; no se conserva histórico de exports.

**Bordes**
- Sin `partner_id` o sin eventos → tabla vacía; CSV solo cabecera (0 filas de datos); no error.
- Sin campo `slide_id` en `survey.user_input` → solo eventos campus.
- Fallo al generar CSV → `UserError`; no dejar attachment a medias usable.

## Seguridad

- Visibilidad de pestaña/acción y ACL: `openeducat_core.group_op_faculty`.
- Cada método de carga/export comprueba `has_group` en servidor; sin grupo → `AccessError`.
- Tras el check, `sudo()` solo lectura sobre modelos de e-learning/survey.
- El CSV no es `public`.
- Sin cambios de autenticación, migraciones de datos, secretos, despliegue ni borrado histórico.

## Pruebas

`TransactionCase` post-install:
- Denegación sin grupo Facultad.
- Filas campus + evaluación presentes y ordenadas por fecha desc.
- Exclusión de contenidos sin `slide.slide.partner` (“No iniciada”).
- Límite 500.
- CSV: cabecera, columnas acordadas, contenido coherente con la UI.

E2E TestSprite: obligatorio (vista XML nueva / pestaña en ficha alumno). Runtime: `docker-compose.local.yml`, puerto 8069, DB desechable; `projectPath` = directorio del módulo.

## Criterios de aceptación

1. En la ficha de alumno, pestaña Actividad muestra historial campus + evaluaciones en orden cronológico (más reciente arriba).
2. Acceso permanece sin cambios de comportamiento por esta misión.
3. Export CSV descarga las mismas columnas/filas (tope 500).
4. Usuario sin Facultad no puede leer ni exportar (server-side).
5. Pruebas de módulo en verde y E2E TestSprite en PASS (scope web/XML obligatorio).

## jev_intake

```json
{"status": "skipped", "skipped_reason": "http_error", "model": null, "mission_class": null, "mission_class_confidence": null, "mission_class_binding": false, "exceeds_simple_limits": false, "exceeds_simple_noul": null, "needs_security_advisor": false, "security_noul": null, "security_keyword_hit": false, "effective_class": null, "effective_class_binding": false}
```

Clasificación orquestador (intake skipped): misión `full`, tier `standard` (módulo nuevo, UI, lectura cross-model, export; sin auth/migraciones/secretos). Security Advisor no forzado por señales de política; el diseño ya fija autorización server-side.
