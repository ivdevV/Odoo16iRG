# Review — Task 4 (Detalle Oficialidad UI)

**Alcance:** UI y vistas en `addons-extra/extrairg/irg_student_oficialidad_documents/` (Task 4), más `groups` en `models/res_partner.py` aplicados como cierre del menor de Task 3.  
**Referencias:** `.superpowers/sdd/task-4-brief.md`, `task-4-report.md`, `reviews/task-4-diff.patch`, `plan.md`, `docs/superpowers/specs/2026-10-15-irg-student-oficialidad-documents-design.md` (§ UI).

**Nota:** No existe `02-progress.md`; se usó el informe SDD, `execution.md` y el diff como registro de cambios.

## Veredicto ejecutivo

| Criterio | Resultado |
| --- | --- |
| **Spec (Task 4 brief + diseño UI)** | ✅ |
| **Decisión** | **Approved** (sin cambios bloqueantes) |

## Hallazgos

### BLOQUEANTE

(Ninguno.)

### MENOR

| ID | Archivo | Qué | Corrección |
| --- | --- | --- | --- |
| M1 | `views/op_student_views.xml` | El One2many solo define subvista `<tree>`; no hay `<form>` embebido como en `irg_student_scholarship_documents/views/op_student_views.xml`. Odoo usará la form standalone (`oficialidad_document_views.xml`); funcional pero el flujo inline puede diferir de becas. | Opcional: añadir subvista `<form>` mínima con `partner_id` invisible y `file`/`filename` para paridad con becas. |
| M2 | `views/oficialidad_document_views.xml` | Menú admin bajo `base.menu_users` (Ajustes → Usuarios) no estaba en el brief obligatorio; puede confundir operativamente. | Confirmar con producto; eliminar menú si solo se opera desde el expediente. |
| M3 | Evidencia (informe Task 4) | Instalación/actualización vía `docker run odoo:16.0`, no el comando canónico `docker compose … odoo_local` de `PROJECT.md`; sin E2E browser en esta fase. | Validator: repetir update con compose canónico si la imagen local está disponible; ejecutar `e2e_testsprite` (obligatorio por scope `views/`). |

### NIT

| ID | Archivo | Qué | Corrección |
| --- | --- | --- | --- |
| N1 | `views/op_student_views.xml` | Se muestra `irg_oficialidad_vat_hint` en el resumen; el diseño enumera tipo, mismatch, completitud y checklist, no el hint explícito. | Aceptable para depuración operativa; ocultar si se prefiere UI más limpia. |
| N2 | `views/op_student_views.xml` | `groups="base.group_user"` en contenedores (group, alert, checklist, O2M), no en cada `<field>` del resumen; los campos del modelo en `res.partner` ya llevan `groups='base.group_user'`. | Coherente con Odoo 16; duplicar `groups` en cada field es redundante. |
| N3 | `models/res_partner.py` (diff Task 4) | `irg_oficialidad_checklist_html` con `sanitize=False` (Task 3): nombres de tipo vienen del catálogo interno; riesgo XSS bajo en backoffice. | Mantener catálogo solo `group_system`; no ampliar edición de nombres a usuarios sin revisión. |

## Comprobaciones explícitas (must verify)

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| Hereda `isep_control_escolar.op_student_form_inh` | ✅ | `op_student_views.xml` L7 / diff L302 |
| Xpath `//page[@name='official_detail']` `position="inside"` | ✅ | L9–38 |
| Bloque `annex_9` / `certificate_type` intacto (sin xpath sobre ellos; contenido nuevo después) | ✅ | Vista padre `isep_control_escolar/views/op_student_view.xml`; herencia solo append inside page |
| Listado descargable: `filename` + `file` con `filename="filename"` | ✅ | Tree L32–33; form admin L245–246 |
| Aviso mismatch VAT (`alert-warning` + `attrs` sobre `irg_oficialidad_type_mismatch`) | ✅ | L19–22; campo soporte invisible L16 |
| `groups` `base.group_user` en campos / UI restringida a internos | ✅ | `res_partner.py`: 10 campos con `groups='base.group_user'`; vista: group/alert/checklist/O2M con `groups="base.group_user"` |
| Campos de vista usables en `op.student` | ✅ | `_inherits` partner (`execution.md` Task 3); test `test_student_related_fields` |
| `__manifest__.py` carga `op_student_views.xml` | ✅ | Tras datos de catálogo |
| Patrón becas (Binary widget, `default_partner_id`: `partner_id`) | ✅ | Alineado con scholarship tree |

## Arquitectura y seguridad (lectura crítica)

- Encaje con plan (tarea 4): herencia correcta de la pestaña existente, prioridad expediente `op.student`, sin portal v1.
- No se toca lógica `annex_9` / `certificate_type`; cumple criterio de aceptación 6 del plan.
- Restricción interna: doble capa razonable (field `groups` + ACL documento; menú admin `base.group_system`).
- Vistas standalone de documento sin `groups` en campos: acceso acotado por ACL y menú system; aceptable.
- Scope diff Task 4 incluye manifest completo y `res_partner.py` (groups): coherente con informe, no rompe arquitectura.

## Veredicto

REVIEW OK
