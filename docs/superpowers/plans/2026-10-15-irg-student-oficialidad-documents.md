# IRG Student Oficialidad Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recibir por webhook la documentación Unimarconi (nacional/internacional) desde oficialidad-app y mostrarla descargable en la pestaña Detalle Oficialidad del expediente, con resumen `X/4` y aviso si el VAT sugiere otro tipo.

**Architecture:** Dos addons espejo de becas: `irg_student_oficialidad_documents` (catálogo, modelo, resumen, UI) y `irg_student_oficialidad_webhook` (`POST /irg/oficialidad/webhook/document`). Odoo confía en `student_type` de la app; el hint DNI/NIE del `vat` solo avisa en UI.

**Tech Stack:** Odoo 16 ORM/HTTP, `ir.config_parameter` Bearer token, Binary attachments, `TransactionCase`, `docker-compose.local.yml`, TestSprite E2E.

## Global Constraints

- Código funcional solo bajo `addons-extra/extrairg/irg_student_oficialidad_documents/` y `addons-extra/extrairg/irg_student_oficialidad_webhook/`.
- No modificar `irg_admission_oficialidad_webhook`, el repo Next.js ni la lógica de `annex_9` / `certificate_type`.
- Heredar la página `official_detail` de `isep_control_escolar` (xpath), no recrearla.
- Versión inicial de ambos módulos: `16.0.1.0.0`. Prefijo de campos/modelos: `irg_oficialidad_*` / `irg.oficialidad.*`.
- Token en `irg_student_oficialidad_webhook.token` (XML vacío, `noupdate`). Comparar con `hmac.compare_digest`.
- `sudo()` solo tras validar token, payload, email, tipo y archivo.
- Límite de archivo 10 MB; extensiones `.pdf`, `.jpg`, `.jpeg`, `.png`, `.doc`, `.docx`.
- Idempotencia: `(partner_id, document_type_id)` → update.
- Runtime de tests: `docker-compose.local.yml`. E2E TestSprite obligatorio; `projectPath` = directorio del módulo documents (vistas), nunca la raíz del repo.
- Misión `full`, tier `complex`. Security Advisor `[YES]` antes de código de producción del webhook.
- Commit / push / PR requieren autorización explícita separada del usuario; no ejecutarlos solo porque el plan liste un checkpoint.

## Knowledge and References

- Spec aprobada: `docs/superpowers/specs/2026-10-15-irg-student-oficialidad-documents-design.md`
- Contrato app: `https://github.com/ivdevV/oficialidad-app` (README + `src/lib/odoo/oficialidad-webhook.ts` + `src/lib/oficialidad-documents.ts`)
- Espejo becas documents: `addons-extra/extrairg/irg_student_scholarship_documents/`
- Espejo becas webhook: `addons-extra/extrairg/irg_student_scholarship_webhook/`
- Doc becas: `doc/modules/extrairg/irg_student_scholarship_webhook.md`
- Página existente: `addons-extra/addons_uisep/isep_control_escolar/views/op_student_view.xml`
- Modding rules: `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`

## File map

| Path | Responsibility |
| --- | --- |
| `.../irg_student_oficialidad_documents/__manifest__.py` | Dependencias y data files |
| `.../models/oficialidad_document_type.py` | Catálogo de tipos |
| `.../models/oficialidad_document.py` | Documento + estados |
| `.../models/res_partner.py` | student_type, docs, resumen, VAT hint |
| `.../models/op_student.py` | Related fields al partner |
| `.../data/oficialidad_document_type_data.xml` | 7 tipos (noupdate) |
| `.../views/op_student_views.xml` | Extiende `official_detail` |
| `.../security/ir.model.access.csv` | ACL backoffice |
| `.../tests/test_oficialidad_documents.py` | Resumen, mismatch, tipos |
| `.../irg_student_oficialidad_webhook/controllers/webhook.py` | Ruta HTTP |
| `.../models/oficialidad_webhook_service.py` | Validación + persistencia |
| `.../tests/test_oficialidad_webhook.py` | Contrato app |
| `missions/irg-student-oficialidad-documents/*` | Artefactos de misión |

## Document type keys (exact)

Nacional: `titulo-universitario`, `certificado-notas`, `matricula-unimarconi`, `documento-identificativo-nacional`  
Internacional: `titulo-universitario-apostillado`, `apostilla-certificado-notas`, `matricula-unimarconi`, `pasaporte`

## VAT hint rule (exact)

Normalize `vat`: strip spaces/dashes/dots, upper-case, drop optional `ES` prefix.

- DNI: `^\d{8}[A-Z]$`
- NIE: `^[XYZ]\d{7}[A-Z]$`
- Match → `nacional`; non-empty non-match → `internacional`; empty → `unknown`

---

### Task 1: Mission shell + Security Advisor gate

**Files:**
- Create: `missions/irg-student-oficialidad-documents/plan.md`
- Create: `missions/irg-student-oficialidad-documents/execution.md`
- Create: `missions/irg-student-oficialidad-documents/artifacts/security-advisor.txt`

**Interfaces:**
- Consumes: this plan + approved design.
- Produces: mission scope and `[YES]` security gate required before Task 5 production webhook code. Tasks 2–4 may scaffold documents module after `[YES]` on the overall design (Advisor reviews webhook auth, token, sudo, ACLs, PII files).

- [ ] **Step 1: Write mission `plan.md`**

Include: objective, acceptance criteria from the design, tier `complex`, roles (coder / reviewer / validator / security advisor / e2e-tester / documenter), E2E trigger YES (views XML), cleanup of temp DB fixtures, and this `jev_intake` block:

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

Note: Security Advisor is still mandatory by `AGENTS.md` (auth/tokens) despite Jev skip.

- [ ] **Step 2: Start `execution.md`**

```bash
git rev-parse HEAD
git status --short --branch
```

Record base commit and that pre-existing dirty files outside this mission stay untouched.

- [ ] **Step 3: Security Advisor review**

Review exactly:

```text
Route: POST /irg/oficialidad/webhook/document auth=none csrf=False
Auth: Bearer vs ir.config_parameter irg_student_oficialidad_webhook.token
Compare: hmac.compare_digest
sudo: only after token+payload+email+type+file validation
Stores: binary student documents (PII) on irg.oficialidad.document
ACL: internal users read/write documents; no portal routes in v1
student_type: trusted from app; VAT mismatch is UI-only warning
No secrets in XML/repo; token param empty noupdate
```

Save verdict to `artifacts/security-advisor.txt`. Last line must be `[YES] Reason: ...`. On `[NO]`, amend plan/spec and re-run before Task 2.

- [ ] **Step 4: Gate check**

```bash
test -f missions/irg-student-oficialidad-documents/plan.md
test -f missions/irg-student-oficialidad-documents/execution.md
tail -n 1 missions/irg-student-oficialidad-documents/artifacts/security-advisor.txt | grep -E '^\[YES\]'
```

Expected: all succeed.

---

### Task 2: Document type catalogue (TDD)

**Files:**
- Create: `addons-extra/extrairg/irg_student_oficialidad_documents/__init__.py`
- Create: `addons-extra/extrairg/irg_student_oficialidad_documents/__manifest__.py`
- Create: `addons-extra/extrairg/irg_student_oficialidad_documents/models/__init__.py`
- Create: `addons-extra/extrairg/irg_student_oficialidad_documents/models/oficialidad_document_type.py`
- Create: `addons-extra/extrairg/irg_student_oficialidad_documents/data/oficialidad_document_type_data.xml`
- Create: `addons-extra/extrairg/irg_student_oficialidad_documents/security/ir.model.access.csv`
- Create: `addons-extra/extrairg/irg_student_oficialidad_documents/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_student_oficialidad_documents/tests/test_oficialidad_document_types.py`

**Interfaces:**
- Produces: model `irg.oficialidad.document.type` with fields `key` (Char, required, index, unique), `name` (Char, required), `student_type_scope` Selection(`nacional`,`internacional`,`both`), `active` Boolean default True; method `get_expected_keys(student_type: str) -> list[str]`.

- [ ] **Step 1: Write failing tests**

```python
# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestOficialidadDocumentTypes(TransactionCase):
    def test_catalogue_has_seven_keys(self):
        Type = self.env['irg.oficialidad.document.type']
        keys = set(Type.search([]).mapped('key'))
        self.assertEqual(keys, {
            'titulo-universitario',
            'certificado-notas',
            'documento-identificativo-nacional',
            'titulo-universitario-apostillado',
            'apostilla-certificado-notas',
            'pasaporte',
            'matricula-unimarconi',
        })

    def test_expected_keys_nacional(self):
        Type = self.env['irg.oficialidad.document.type']
        self.assertEqual(
            Type.get_expected_keys('nacional'),
            [
                'titulo-universitario',
                'certificado-notas',
                'matricula-unimarconi',
                'documento-identificativo-nacional',
            ],
        )

    def test_expected_keys_internacional(self):
        Type = self.env['irg.oficialidad.document.type']
        self.assertEqual(
            Type.get_expected_keys('internacional'),
            [
                'titulo-universitario-apostillado',
                'apostilla-certificado-notas',
                'matricula-unimarconi',
                'pasaporte',
            ],
        )

    def test_matricula_scope_both(self):
        matricula = self.env['irg.oficialidad.document.type'].search([
            ('key', '=', 'matricula-unimarconi'),
        ], limit=1)
        self.assertEqual(matricula.student_type_scope, 'both')
```

- [ ] **Step 2: Run RED**

```bash
docker compose -f docker-compose.local.yml exec -T odoo odoo \
  -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_student_oficialidad_documents \
  --test-enable --stop-after-init \
  --test-tags=/irg_student_oficialidad_documents \
  --db_host=pgodoo_latest
```

Expected: FAIL (module/model missing) or adjust compose service names to the local stack; record the exact command that works in `execution.md`.

- [ ] **Step 3: Implement catalogue**

`oficialidad_document_type.py`:

```python
# -*- coding: utf-8 -*-
from odoo import api, fields, models


class IrgOficialidadDocumentType(models.Model):
    _name = 'irg.oficialidad.document.type'
    _description = 'Tipo de documento de oficialidad IRG'
    _order = 'id'

    key = fields.Char(required=True, index=True)
    name = fields.Char(required=True, translate=True)
    student_type_scope = fields.Selection(
        selection=[
            ('nacional', 'Nacional'),
            ('internacional', 'Internacional'),
            ('both', 'Ambos'),
        ],
        required=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('key_uniq', 'unique(key)', 'La clave del tipo de documento debe ser unica.'),
    ]

    @api.model
    def get_expected_keys(self, student_type):
        if student_type not in ('nacional', 'internacional'):
            return []
        types = self.search([
            ('active', '=', True),
            ('student_type_scope', 'in', [student_type, 'both']),
        ])
        # Stable order matching the app README tables
        order = {
            'nacional': [
                'titulo-universitario',
                'certificado-notas',
                'matricula-unimarconi',
                'documento-identificativo-nacional',
            ],
            'internacional': [
                'titulo-universitario-apostillado',
                'apostilla-certificado-notas',
                'matricula-unimarconi',
                'pasaporte',
            ],
        }[student_type]
        by_key = {rec.key: rec for rec in types}
        return [key for key in order if key in by_key]
```

XML data: one record per key with matching `student_type_scope` (`matricula-unimarconi` → `both`). Manifest depends: `base`, `openeducat_core`, `isep_control_escolar`. Load security CSV + data XML.

ACL: `base.group_user` read on types; system write optional (types are data).

- [ ] **Step 4: Run GREEN** — same command as Step 2; expect 4 passed.

- [ ] **Step 5: Record evidence** in `missions/irg-student-oficialidad-documents/artifacts/types-tests.txt` and update `execution.md`.

---

### Task 3: Document model + partner summary (TDD)

**Files:**
- Create: `.../models/oficialidad_document.py`
- Create: `.../models/res_partner.py`
- Create: `.../models/op_student.py`
- Modify: `.../models/__init__.py`
- Modify: `.../security/ir.model.access.csv`
- Create: `.../tests/test_oficialidad_summary.py`

**Interfaces:**
- Produces: `irg.oficialidad.document` with `partner_id`, `document_type_id`, `name`, `filename`, `file`, `note`, `state`.
- Partner fields: `irg_oficialidad_student_type`, `irg_oficialidad_document_ids`, computed summary fields listed in the design, plus `irg_oficialidad_checklist_html`.
- Helper on partner: `_irg_oficialidad_vat_hint_from_vat(vat: str) -> str`.

- [ ] **Step 1: Failing tests**

```python
# -*- coding: utf-8 -*-
import base64
from odoo.tests.common import TransactionCase


class TestOficialidadSummary(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Alumno Oficialidad',
            'email': 'oficialidad.alumno@example.com',
            'vat': '12345678Z',
        })
        self.type_titulo = self.env['irg.oficialidad.document.type'].search([
            ('key', '=', 'titulo-universitario'),
        ], limit=1)

    def test_vat_hint_dni_nacional(self):
        hint = self.partner._irg_oficialidad_vat_hint_from_vat('12345678Z')
        self.assertEqual(hint, 'nacional')

    def test_vat_hint_nie_nacional(self):
        hint = self.partner._irg_oficialidad_vat_hint_from_vat('X1234567L')
        self.assertEqual(hint, 'nacional')

    def test_vat_hint_foreign_internacional(self):
        hint = self.partner._irg_oficialidad_vat_hint_from_vat('AB123456')
        self.assertEqual(hint, 'internacional')

    def test_mismatch_when_app_says_internacional(self):
        self.partner.irg_oficialidad_student_type = 'internacional'
        self.assertTrue(self.partner.irg_oficialidad_type_mismatch)

    def test_completeness_after_one_document(self):
        self.partner.irg_oficialidad_student_type = 'nacional'
        self.env['irg.oficialidad.document'].create({
            'partner_id': self.partner.id,
            'document_type_id': self.type_titulo.id,
            'name': 'Titulo universitario',
            'filename': 'titulo.pdf',
            'file': base64.b64encode(b'%PDF-1.4 test'),
        })
        self.assertEqual(self.partner.irg_oficialidad_expected_count, 4)
        self.assertEqual(self.partner.irg_oficialidad_received_count, 1)
        self.assertEqual(self.partner.irg_oficialidad_completeness, '1/4')
        self.assertFalse(self.partner.irg_oficialidad_is_complete)
```

- [ ] **Step 2: RED** — install/update module with `--test-tags` for this class; expect FAIL on missing fields/model.

- [ ] **Step 3: Implement models**

Document model mirrors scholarship document (states + `name_get`). Partner computes:

```python
@api.model
def _irg_oficialidad_vat_hint_from_vat(self, vat):
    import re
    if not vat:
        return 'unknown'
    normalized = re.sub(r'[\s.\-]', '', vat).upper()
    if normalized.startswith('ES'):
        normalized = normalized[2:]
    if re.match(r'^\d{8}[A-Z]$', normalized) or re.match(r'^[XYZ]\d{7}[A-Z]$', normalized):
        return 'nacional'
    return 'internacional'
```

`received_count`: number of expected keys that have at least one document for the partner.  
`checklist_html`: readonly HTML `<ul>` of expected types with Recibido/Pendiente and state.  
`op.student`: related fields from `partner_id` for UI binding.

ACL: `base.group_user` CRUD on `irg.oficialidad.document`; read on types.

- [ ] **Step 4: GREEN** + save `artifacts/summary-tests.txt`.

---

### Task 4: Detalle Oficialidad UI + downloadable list

**Files:**
- Create: `.../views/op_student_views.xml`
- Create: `.../views/oficialidad_document_views.xml` (optional menu for admins)
- Modify: `__manifest__.py` to load views

**Interfaces:**
- Consumes: partner/student related fields from Task 3.
- Produces: xpath into `//page[@name='official_detail']` appending summary + One2many with `file`/`filename`.

- [ ] **Step 1: Write view inheritance**

```xml
<record id="view_op_student_form_oficialidad_documents" model="ir.ui.view">
  <field name="name">op.student.form.oficialidad.documents</field>
  <field name="model">op.student</field>
  <field name="inherit_id" ref="isep_control_escolar.op_student_form_inh"/>
  <field name="arch" type="xml">
    <xpath expr="//page[@name='official_detail']" position="inside">
      <group string="Solicitud de oficialidad">
        <group>
          <field name="irg_oficialidad_student_type" readonly="1"/>
          <field name="irg_oficialidad_completeness" readonly="1"/>
          <field name="irg_oficialidad_last_received_at" readonly="1"/>
          <field name="irg_oficialidad_vat_hint" readonly="1"/>
          <field name="irg_oficialidad_type_mismatch" invisible="1"/>
        </group>
      </group>
      <div class="alert alert-warning" role="alert"
           attrs="{'invisible': [('irg_oficialidad_type_mismatch', '=', False)]}">
        El identificador fiscal (VAT/DNI) sugiere un tipo de alumno distinto al
        indicado en la solicitud de oficialidad. Revisa el expediente.
      </div>
      <field name="irg_oficialidad_checklist_html" nolabel="1" readonly="1"/>
      <field name="irg_oficialidad_document_ids" mode="tree,form"
              context="{'default_partner_id': partner_id}">
        <tree>
          <field name="create_date" readonly="1"/>
          <field name="document_type_id"/>
          <field name="name"/>
          <field name="filename"/>
          <field name="file" filename="filename"/>
          <field name="state"/>
          <field name="note"/>
        </tree>
      </field>
    </xpath>
  </field>
</record>
```

Ensure `op.student` exposes every field used (related to partner). Keep existing `annex_9` group untouched above the new block.

- [ ] **Step 2: Syntax / update check**

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('addons-extra/extrairg/irg_student_oficialidad_documents/views/op_student_views.xml')"
docker compose -f docker-compose.local.yml exec -T odoo odoo \
  -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_student_oficialidad_documents --stop-after-init --db_host=pgodoo_latest
```

Expected: XML parses; module updates without error.

- [ ] **Step 3: Note in `execution.md`** that download uses standard Binary widget (`file` + `filename`), same as becas.

---

### Task 5: Webhook service + controller (TDD)

**Files:**
- Create: entire `addons-extra/extrairg/irg_student_oficialidad_webhook/` package mirroring scholarship webhook layout
- Create: `data/oficialidad_webhook_params.xml` with empty token (`noupdate`)
- Create: `tests/test_oficialidad_webhook.py`

**Interfaces:**
- Consumes: document types + document model from documents module.
- Produces: `irg.oficialidad.webhook.service` with `validate_authorization(header) -> dict|None` and `process_payload(payload) -> (dict, status)`; route `/irg/oficialidad/webhook/document`.

- [ ] **Step 1: Failing tests** (mirror scholarship tests; adapt fields)

Cover at minimum:

1. missing/invalid/unconfigured token → 401  
2. partner_not_found / ambiguous_email  
3. missing `student_type` / invalid → 400 `invalid_student_type`  
4. unknown `document_type_key` → 404 `document_type_not_found`  
5. `titulo-universitario-apostillado` with `student_type=nacional` → 409 `document_type_student_type_mismatch`  
6. create then same type again → `updated`  
7. persists `irg_oficialidad_student_type` on partner  
8. invalid base64 / bad extension / empty / too large  

Use `base64.b64encode(b'%PDF-1.4 x')` and partner+student fixtures like scholarship tests.

- [ ] **Step 2: RED** with `-i irg_student_oficialidad_webhook --test-tags=/irg_student_oficialidad_webhook`.

- [ ] **Step 3: Implement service**

Copy structure from `scholarship_webhook_service.py` with these differences:

- Param: `irg_student_oficialidad_webhook.token`
- Required: `email`, `filename`, `document_content_base64`, `document_type_key`, `student_type`
- Resolve type by exact `key` (active)
- Scope check: type.scope in (`both`, student_type) else mismatch 409
- Idempotent search: `partner_id` + `document_type_id`
- On success: `partner.write({'irg_oficialidad_student_type': student_type})`
- Do **not** fail on VAT mismatch

Controller identical pattern to scholarship (`type='http'`, `auth='none'`, `csrf=False`, JSON response).

- [ ] **Step 4: GREEN** + `artifacts/webhook-tests.txt`.

---

### Task 6: Independent review + validation + E2E

**Files:**
- Create: `missions/irg-student-oficialidad-documents/verification.json`
- Create: `missions/irg-student-oficialidad-documents/artifacts/*.txt` evidence
- Create: `missions/irg-student-oficialidad-documents/artifacts/e2e-testsprite.txt`

**Interfaces:**
- Consumes: green module tests from Tasks 2–5.
- Produces: `verification.json` with `status: passed` only if no check fails.

- [ ] **Step 1: Code review** by an agent/person distinct from the coder. Scope: production code, tests, security, views. No approval with blocking notes.

- [ ] **Step 2: Validator re-runs** (do not trust prior logs):

```bash
# Adjust service/db names to local compose
docker compose -f docker-compose.local.yml exec -T odoo odoo \
  -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_student_oficialidad_documents,irg_student_oficialidad_webhook \
  --test-enable --stop-after-init \
  --test-tags=/irg_student_oficialidad_documents,/irg_student_oficialidad_webhook \
  --db_host=pgodoo_latest
```

- [ ] **Step 3: E2E TestSprite** via `e2e-tester` subagent against local `8069` disposable DB. `projectPath` = `addons-extra/extrairg/irg_student_oficialidad_documents`. Never beta/prod. Cleanup fixtures after.

- [ ] **Step 4: Write `verification.json`** with checks `unit_types`, `unit_summary`, `unit_webhook`, `module_update`, `e2e_testsprite`, environment, `model_tier_used: complex`.

---

### Task 7: Documentation

**Files:**
- Create: `doc/modules/extrairg/irg_student_oficialidad_webhook.md`
- Create: `addons-extra/extrairg/irg_student_oficialidad_documents/README.md` (short)
- Create: `missions/irg-student-oficialidad-documents/CHANGELOG.md`
- Optional knowledge: `.agents/knowledge/odoo_development_modding/artifacts/irg_student_oficialidad_webhook.md` only if there is a reusable gotcha (token + student_type trust + VAT warn-only)

- [ ] **Step 1: Module docs** — endpoint, payload, keys table, errors, install curl example (mirror scholarship doc style; no real tokens).

- [ ] **Step 2: CHANGELOG** mission entry summarizing behavior.

- [ ] **Step 3: Final git coherence check** (no commit unless user authorizes):

```bash
git status --short
git diff --stat
```

---

## Self-review (plan vs spec)

| Spec requirement | Task |
| --- | --- |
| Two modules documents + webhook | 2–5 |
| Catalogue 7 keys + nacional/internacional | 2 |
| Trust app `student_type`, VAT mismatch warn-only | 3, 5 |
| Summary `X/4` + checklist | 3–4 |
| Inherit Detalle Oficialidad, keep annex_9 | 4 |
| Downloadable binaries | 4 |
| Webhook contract + errors | 5 |
| Security Advisor + Bearer | 1, 5 |
| Tests + E2E | 2–3, 5–6 |
| Docs | 7 |
| Out of scope (portal, n8n outbound, Next.js) | Global Constraints |

No TBD placeholders remain. Field names are consistent across tasks (`irg_oficialidad_*`, `irg.oficialidad.*`).
