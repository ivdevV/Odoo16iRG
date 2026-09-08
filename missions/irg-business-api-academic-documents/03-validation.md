# Validación — irg-business-api-academic-documents

**Validador independiente** (no el coder, no el revisor)  
**Fecha:** 2026-09-08  
**Runtime:** `docker-compose.local.yml` / servicio `odoo_local` / DB `test_irg_api_gradebook_cert`  
**Base commit:** `df9c34d02dcee99b1741723769c79fb1bd78dd9a`

---

## Check 1: py_compile (sintaxis)

**Resultado: PASS**

Archivos verificados:
- `models/document_service.py`
- `models/api_constants.py`
- `models/api_operation.py`
- `models/gradebook_service.py`
- `tests/test_academic_documents.py`
- `tests/test_gradebook_certificate.py`

Salida: vacía (sin errores). Exit code: 0.  
Evidencia: `artifacts/validation-py-compile.txt`

---

## Check 2: Tests de módulo (Odoo --test-enable)

**Resultado: PASS**

```
0 failed, 0 error(s) of 72 tests
```

### Tests saltados (skipTest)

| Test | Razón | Justificación |
|------|-------|--------------|
| `test_attendance_approve_on_hc_admission` | "Attendance certificates are not installed." | Correcto. El módulo `irg_certificate_attendance` no se instala en esta DB porque arrastra `website`/portal/Stripe. El skip es parte del diseño: el test guarda la razón en `skipTest` y se activará cuando el módulo esté presente. |
| `test_attendance_requires_session_id` | "Attendance certificates are not installed." | Ídem. |

### Tests de diploma que ejecutaron (no saltados)

| Test | Estado |
|------|--------|
| `test_diploma_rejects_running_course` | **RAN — PASS** |
| `test_diploma_approve_returns_private_pdf` | **RAN — PASS** |
| `test_diploma_preview_has_no_gradebook_and_no_pdf` | **RAN — PASS** |
| `test_diploma_unknown_payload_key_rejected` | **RAN — PASS** |
| `test_enrollment_approve_returns_private_pdf` | **RAN — PASS** |
| `test_enrollment_uses_admission_not_gradebook_payload` | **RAN — PASS** |

### Tests de rechazo de tipo en comando de notas

| Test | Estado |
|------|--------|
| `test_notes_command_rejects_diploma_type` | **RAN — PASS** |
| `test_notes_command_rejects_enrollment_type` | **RAN — PASS** |

Evidencia: `artifacts/validation-tests.txt`

---

## Check 3: Scope del diff (git porcelain)

**Resultado: PASS**

```
 M addons-extra/extrairg/irg_business_api/__manifest__.py
 M addons-extra/extrairg/irg_business_api/models/api_constants.py
 M addons-extra/extrairg/irg_business_api/models/api_operation.py
 M addons-extra/extrairg/irg_business_api/models/gradebook_service.py
 M addons-extra/extrairg/irg_business_api/tests/__init__.py
 M addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py
?? addons-extra/extrairg/irg_business_api/models/document_service.py
?? addons-extra/extrairg/irg_business_api/tests/test_academic_documents.py
```

Todos los cambios en `addons-extra/` son exclusivamente dentro de `irg_business_api`. Ningún otro módulo tocado.

---

## Check 4: Criterios de aceptación de la spec

**Resultado: PASS**

| Criterio | Verificación |
|----------|-------------|
| Tres nuevos códigos de operación (`irg_generate_diploma`, `irg_generate_enrollment_certificate`, `irg_generate_attendance_certificate`) | Presentes en `api_constants.py` líneas 74-76 y 167-195 |
| Comando de notas rechaza tipos diploma/enrollment/attendance | `gradebook_service.py` línea 106-109: `MOVED_DOCUMENT_TYPES` con mensaje de redirección; tests `test_notes_command_rejects_diploma_type` y `test_notes_command_rejects_enrollment_type` PASS |
| Diploma exige curso finalizado | `document_service.py` línea 259: `course.state != 'finished'` lanza `UserError`; `test_diploma_rejects_running_course` RAN y PASS |
| `file_b64` privado | `document_service.py` línea 43: `raise UserError` si adjunto no es privado; `bin_size=False` para obtener datos binarios reales |

---

## Check 5: E2E TestSprite

**Resultado: SKIPPED**

Justificación: El diff toca exclusivamente modelos Python, tests y manifest. No hay vistas QWeb, templates, assets estáticos, controladores HTTP ni portal. El plan declaró E2E skipped por este scope. Conforme al contrato de verificación de `AGENTS.md`.

---

## Veredicto global

**PASS global**

Todos los checks ejecutables pasan. Los 2 tests de asistencia HC están correctamente justificados con `skipTest` por ausencia del módulo. Los tests críticos de diploma y matrícula ejecutaron y pasaron. Ningún fallo, ningún error.
