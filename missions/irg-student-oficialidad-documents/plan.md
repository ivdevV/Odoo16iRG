# Plan — irg-student-oficialidad-documents

## Objetivo

Recibir desde la aplicación Next.js de oficialidad
([ivdevV/oficialidad-app](https://github.com/ivdevV/oficialidad-app)) la
documentación Unimarconi de cada alumno vía webhook inbound y mostrarla en la
pestaña **Detalle Oficialidad** (`page[@name='official_detail']`) del
expediente `op.student`, con resumen de completitud (`X/4`) y distinción
nacional/internacional. Replica el patrón de becas
(`irg_student_scholarship_documents` / `irg_student_scholarship_webhook`).

Diseño aprobado: `docs/superpowers/specs/2026-10-15-irg-student-oficialidad-documents-design.md`.

Módulos:

- `irg_student_oficialidad_documents` (deps: `openeducat_core`, `isep_control_escolar`): modelo de documento, catálogo de tipos, campos de partner/student, resumen, UI.
- `irg_student_oficialidad_webhook` (dep: `irg_student_oficialidad_documents`): endpoint `POST /irg/oficialidad/webhook/document` (Bearer + JSON).

Fuera de alcance: portal Campus, pull hacia Sheets/API de lectura, cambios en
`irg_admission_oficialidad_webhook` (outbound), cambios en el repo Next.js,
lógica de negocio de `annex_9` / `certificate_type`.

## Clasificación

- Clase: `full` (feature nueva, comportamiento de producto, cross-module, seguridad).
- Tier: **`complex`** (>5 archivos, webhook público + token + sudo + PII + UI + catálogo).
- Rama: `feat/irg-student-oficialidad-documents`.
- Jev intake: `skipped` (`http_error`); se clasifica por política `AGENTS.md`.
  El Security Advisor sigue siendo obligatorio por política (autenticación/token/secreto) aunque Jev se omita.

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

## Criterios de aceptación (del diseño)

1. Con token válido, la app puede enviar los 4 documentos de un alumno nacional o internacional y quedan en el expediente bajo **Detalle Oficialidad**.
2. El listado permite descargar cada archivo.
3. Se muestra el tipo de alumno y la completitud `X/4` según el tipo.
4. Si el `vat` sugiere otro tipo, hay aviso visible y el webhook no falla.
5. Reenviar el mismo `document_type_key` actualiza el documento (`action=updated`).
6. `annex_9` / `certificate_type` siguen funcionando.
7. Tests Odoo en GREEN y check `e2e_testsprite` en PASS.

Contrato webhook (resumen): `POST /irg/oficialidad/webhook/document`,
`Authorization: Bearer <token>` (`irg_student_oficialidad_webhook.token`,
`hmac.compare_digest`), JSON con `email`, `filename`, `document_content_base64`,
`document_type_key`, `student_type` obligatorios; extensiones
`.pdf/.jpg/.jpeg/.png/.doc/.docx`, máx. 10 MB; errores 401/400/413/404/409 según el diseño.

## Roles

| Rol | Responsabilidad |
| --- | --- |
| Orquestador | Plan, clasificación, gates, artefactos de misión |
| Security Advisor | Revisión previa a Implementación (auth pública, token, sudo, PII). Veredicto en `artifacts/security-advisor.txt`; bloquea con `[NO]` |
| Coder | Implementación TDD (RED → GREEN → refactor) de ambos módulos |
| Reviewer | Revisión independiente del código y elementos funcionales (una vez por versión funcional) |
| Validator | Repite checks sin confiar en resultados previos; emite `verification.json` |
| E2E tester | Check `e2e_testsprite` con TestSprite MCP (`.claude/agents/e2e-tester.md`) |
| Documenter | Uso, configuración, pruebas, limitaciones, `CHANGELOG.md`, knowledge reutilizable |

## Tareas (alto nivel)

1. Mission shell + Security Advisor gate (esta tarea).
2. Scaffold `irg_student_oficialidad_documents`: catálogo de tipos (XML `noupdate`), modelo `irg.oficialidad.document`, ACL.
3. Campos de partner/student, resumen, hint VAT y `type_mismatch`.
4. UI: herencia `isep_control_escolar.op_student_form_inh` → `official_detail` (resumen, checklist, listado descargable).
5. Módulo `irg_student_oficialidad_webhook`: servicio + controlador + parámetro de token (vacío, `noupdate`).
6. Tests Odoo, E2E, validación, documentación.

Las tareas 2–4 pueden avanzar tras `[YES]`; la tarea 5 (código de webhook en producción) requiere `[YES]` del Security Advisor.

## Pruebas

- Suite Odoo (`TransactionCase` / HTTP según patrón de becas) en `docker-compose.local.yml`: token ausente/inválido/no configurado; email inexistente/ambiguo; `student_type` ausente/inválido; `document_type_key` desconocido/incompatible; create + update idempotente (partner + tipo); persistencia de `student_type`, `X/4` y última recepción; hint VAT DNI/NIE y `type_mismatch` sin bloquear; límites de archivo (extensión, vacío, tamaño, base64).
- Lint/sintaxis de Python y XML de los módulos nuevos.

## Disparo E2E: **SÍ**

El diff toca vistas XML (`views/`) del expediente `op.student`, por lo que el check
`e2e_testsprite` es obligatorio (AGENTS.md, «Capa E2E»). Se ejecuta tras el resto de
checks de validación y solo si ninguno falló. Límites: `projectPath` = directorio del
módulo de la misión (nunca raíz del repo ni `etc/`, `docker/`, `docker-compose*.yml`);
runtime local `docker-compose.local.yml` en el puerto `8069`; base de datos desechable;
prohibido apuntar a beta/producción; credenciales de `needLogin` de un usuario
desechable de la base local.

## Limpieza (cleanup)

Al finalizar validación y E2E: eliminar de la base temporal los fixtures creados
(partners/alumnos de prueba, documentos `irg.oficialidad.document`, usuarios E2E,
parámetro de token de prueba), restaurar `irg_student_oficialidad_webhook.token` a
vacío/estado original, restaurar el servicio/compose original si se usó overlay de
worktree y registrar evidencia de limpieza y restauración en `artifacts/`.
Ninguna prueba debe dejar el entorno compartido apuntando a un worktree.

## Seguridad

Security Advisor obligatorio antes de Implementación (ruta `auth='none'`, CSRF
desactivado, token compartido, `sudo` tras validación, ficheros binarios con PII).
Veredicto: `artifacts/security-advisor.txt`.

## Artefactos

`plan.md`, `execution.md`, `artifacts/`, `verification.json`, `CHANGELOG.md` y
documentación/knowledge cuando correspondan. Knowledge base: consultar
`.agents/knowledge/odoo_development_modding/artifacts/` en la fase de documentación.

## Autorización

No se hace commit, push ni PR sin autorización explícita del usuario.
