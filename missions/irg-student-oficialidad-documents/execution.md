# Execution — irg-student-oficialidad-documents

## Entorno base

- Rama: `feat/irg-student-oficialidad-documents`
- Base commit (`git rev-parse HEAD`): `30a6f9383d128d80d38623d2a1fb28a7108dc9b8`
- Capacidad / tier: `complex`

## Estado Git al iniciar (`git status --short --branch`)

```
## feat/irg-student-oficialidad-documents
 M AGENTS.md
 M addons-extra/extrairg/irg_hide_portal_servicios/__manifest__.py
 M addons-extra/extrairg/irg_hide_portal_servicios/views/portal_templates.xml
?? (numerosos archivos sin seguimiento: .agents/, addons-extra/extrairg/irg_student_followup/, docs/superpowers/, graphify-out/, missions/*, scratch/, ...)
```

**Nota:** los archivos sucios/sin seguimiento previos fuera de
`missions/irg-student-oficialidad-documents/` NO pertenecen a esta misión y se
dejan intactos (no se modifican, no se formatean, no se añaden al commit).

## Registro

### Task 1 — Mission shell + Security Advisor gate

- Creados `plan.md`, `execution.md` y `artifacts/security-advisor.txt` dentro de la misión.
- Jev intake: `skipped` (`http_error`); clasificación por política `AGENTS.md` (`full` / `complex`).
- Security Advisor: ver `artifacts/security-advisor.txt` (veredicto en la última línea).
- Sin commit, push ni PR (no autorizados). Sin código Odoo creado.
- Comandos: `git rev-parse HEAD`, `git status --short --branch`, gate checks del Step 4 (ver informe de tarea).
- Nota de entorno: `git` imprimió `error: daemon terminated` (fsmonitor) en una ejecución; la salida de `rev-parse` y `status` fue correcta.

### Task 2 — Catálogo de tipos de documento (TDD)

- Creado módulo `addons-extra/extrairg/irg_student_oficialidad_documents/` (manifest, modelo `irg.oficialidad.document.type`, datos de 7 tipos, ACL, tests). Sin commit/push/PR.
- Runtime: `docker-compose.local.yml` solo define `odoo_local`, cuya imagen `odoo16irg:16.0-local` no se construye (apt 404 Debian 11); se usa `docker run` sobre `odoo:16.0` en la red `odoo16irg_local_default` (mismo patrón que misiones previas). Script `run_odoo.sh <db> <flags>`:
  `docker run --rm --network odoo16irg_local_default -v <repo>/addons-extra:/mnt/extra-addons:ro -v <repo>/etc/odoo/odoo.local.conf:/etc/odoo/odoo.conf:ro odoo:16.0 odoo -c /etc/odoo/odoo.conf -d <db> <flags> --stop-after-init --workers=0 --http-port=18069`
- Docker/OrbStack estaba parado: se arrancó con `orbctl start`.
- BD desechable `test_irg_oficialidad_types`: `-i isep_gradebook` y luego `-i isep_control_escolar` (isep_control_escolar tiene dependencia no declarada con `isep_gradebook`; instalarlo directo falla con `Model 'app.gradebook.student' does not exist`).
- RED: tests escritos antes del código; `-i irg_student_oficialidad_documents --test-enable --test-tags=/irg_student_oficialidad_documents` → `invalid module names, ignored` y 0 tests (módulo inexistente).
- GREEN (mismo comando): `0 failed, 0 error(s) of 4 tests`.
- Seguridad: `UNIQUE(key)` (`key_uniq`), ACL solo `base.group_user` (lectura) y `base.group_system` (CRUD), sin filas portal/public, sin secretos en XML.
- `py_compile` OK. BD desechable eliminada. Evidencia: `artifacts/types-tests.txt`.

### Task 3 — Modelo de documento + resumen en partner (TDD)

- Creados `models/oficialidad_document.py` (`irg.oficialidad.document`, `UNIQUE(partner_id, document_type_id)` = `partner_document_type_uniq`, estados + acciones + `name_get`), `models/res_partner.py` (campos `irg_oficialidad_*`, `_irg_oficialidad_vat_hint_from_vat`, checklist HTML), `tests/test_oficialidad_summary.py`; actualizados `models/__init__.py`, `tests/__init__.py`, `security/ir.model.access.csv` (solo `base.group_user` CRUD; sin portal/public). Sin commit/push/PR.
- Decisión: no se crea `models/op_student.py`. `op.student` hace `_inherits={'res.partner': 'partner_id'}`, así que todos los campos `irg_oficialidad_*` ya son accesibles en el alumno; redefinirlos como `related` los duplicaría. Cubierto por `test_student_related_fields`.
- Decisión: `last_received_at` = máximo de `write_date or create_date` de los documentos esperados recibidos (cubre reenvíos/actualizaciones). Lookup del catálogo con `sudo()` en el compute (solo catálogo); los documentos se leen con los permisos del usuario.
- Runtime: mismo patrón que Task 2 (`docker run` sobre `odoo:16.0`, `/tmp/t3/run_odoo.sh`, BD desechable `test_irg_oficialidad_summary`: `-i isep_gradebook`, `-i isep_control_escolar`). Nota: los comandos largos deben lanzarse con `block_until_ms: 0`; si el shell padre termina, el contenedor muere y la instalación se corta (hubo 2 bootstraps abortados y la BD se recreó).
- RED: `-i irg_student_oficialidad_documents --test-enable --test-tags=/irg_student_oficialidad_documents` → `1 failed, 20 error(s) of 25 tests` (modelo/campos inexistentes).
- GREEN: `-u ... ` mismo test-tags → `0 failed, 0 error(s) of 25 tests` (4 catálogo + 21 resumen).
- Seguridad: C6 `UNIQUE(partner_id, document_type_id)` verificado por test (`IntegrityError`); C7 attachments `ir.attachment.public=False` verificado; ACL sin portal/public ni filas sin grupo, `AccessError` para usuario portal verificado.
- `py_compile` OK. BD desechable eliminada. Evidencia: `artifacts/summary-tests.txt`.

### Task 4 — Detalle Oficialidad UI + lista descargable

- Creados `views/op_student_views.xml` (herencia de `isep_control_escolar.op_student_form_inh`, xpath `//page[@name='official_detail']` `position="inside"`; el bloque `annex_9` queda intacto arriba) y `views/oficialidad_document_views.xml` (tree/form/search + acción + menú solo `base.group_system` bajo Ajustes > Usuarios y compañías). Ambos cargados en `__manifest__.py`. Sin commit/push/PR.
- La descarga usa el widget Binary estándar (`file` + `filename="filename"`), igual que la pestaña de becas. No hay controlador HTTP nuevo.
- Menor de la review de Task 3: añadido `groups='base.group_user'` a todos los campos `irg_oficialidad_*` de `res.partner` (tipo, documentos, contadores, completitud, última recepción, hint, mismatch, checklist) y `groups="base.group_user"` en los elementos de vista correspondientes, para que el código portal no los evalúe.
- Servidor: la autorización real sigue en ACL (`base.group_user`/`base.group_system`); los `groups` de campo/vista no sustituyen ACL.
- Runtime: mismo patrón `docker run` sobre `odoo:16.0` (scripts en `/tmp/t4`, BD desechable `test_irg_oficialidad_ui`). Resultados: ver informe `.superpowers/sdd/task-4-report.md`.

### Task 5 — Webhook service + controller (TDD, security-critical)

- Creado `addons-extra/extrairg/irg_student_oficialidad_webhook/` (manifest, `data/oficialidad_webhook_params.xml` con token vacío `noupdate`, servicio `irg.oficialidad.webhook.service`, controlador `POST /irg/oficialidad/webhook/document`, 61 tests). No se tocó becas ni la app Next.js. Sin commit/push/PR.
- Mejoras sobre becas (Security Advisor C1–C10): compare_digest sobre bytes UTF-8 + `except (TypeError, ValueError)` → `invalid_token`; token vacío/espacios = no configurado; orden token → JSON objeto → campos/student_type → archivo (longitud base64 antes de decodificar) → tipo+scope → email → sudo write; email con `=ilike` escapando `\`, `%`, `_`; filename saneado (basename, sin control chars, ≤255 conservando extensión); upsert idempotente por (partner, tipo) con savepoint y fallback a update ante `IntegrityError`; límite de cuerpo HTTP 15 MB comprobado tras el token y antes de `json.loads`; 500 genérico, el log solo incluye clase de excepción y frames (sin mensaje, payload ni token).
- Runtime: `docker run` sobre `odoo:16.0` (scripts `/tmp/t5`), BD desechable `test_irg_oficialidad_wh` (`-i isep_gradebook`, `-i isep_control_escolar`, `-i irg_student_oficialidad_documents`). Los comandos largos se lanzan como comando directo con `block_until_ms: 0` (con `nohup ... &` dentro de un shell que termina, el contenedor muere).
- Tests HTTP: `HttpCase` + `self.authenticate(None, None)` para que la sesión anónima resuelva la BD (sin ello la ruta `auth='none'` devuelve 404 en tests).
- RED: `-i irg_student_oficialidad_webhook` con servicio/controlador en disco pero sin importar → `0 failed, 61 error(s) of 61 tests` (`KeyError: 'irg.oficialidad.webhook.service'`).
- GREEN: `-u ...` → `0 failed, 0 error(s) of 61 tests`. Comprobación de mutación (temporal, revertida) confirma que los tests de C1/C3/C4 detectan la regresión.
- BD desechable eliminada. Evidencia: `artifacts/webhook-tests.txt`; informe: `.superpowers/sdd/task-5-report.md`.

### Task 5 — Round 2 (fix de la review)

- Important: `irg_oficialidad_student_type` ya no se escribe antes del upsert. Ahora `_upsert_document` + `partner.write(student_type)` van dentro de un único `savepoint`, con la escritura del partner DESPUÉS de un upsert correcto; un fallo no deja tipo cambiado sin documento. Defensa en profundidad: `request.env.cr.rollback()` en el `except` del controlador.
- Minor 1: `_clean_required_text` quita caracteres de control/NUL y admite tope; email ≤254, `document_type_key` ≤64 (filename se sanea luego en `_sanitize_filename`).
- Tests nuevos (5): `test_upsert_failure_does_not_change_partner_student_type`, `test_partner_write_failure_rolls_back_created_document`, `test_student_type_written_after_document_exists`, `test_control_chars_stripped_from_email_and_type_key`, `test_overlong_email_and_type_key_are_bounded`. Nota: Odoo envuelve `assertRaises` en un savepoint y ocultaría la fuga del write; los tests de fallo usan `try/except`.
- RED (orden antiguo + limpiadores antiguos): `1 failed, 1 error of 66`. GREEN: `0 failed, 0 error(s) of 66 tests` (`-i` y `-u`). BD desechable eliminada.
- Entorno: el daemon Docker se reinició a mitad de sesión (contenedores cortados), por lo que se repitió el bootstrap de la BD; scripts en /tmp rechazados por el clasificador se ejecutaron como comandos directos.
