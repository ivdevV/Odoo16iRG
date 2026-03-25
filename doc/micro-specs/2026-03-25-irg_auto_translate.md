# Micro-spec: irg_auto_translate — OpenEduCat Content Translation Automation

**Date:** March 25, 2026  
**Module:** `irg_auto_translate` (skeleton)  
**Version:** 16.0.1.0.0  
**Author:** IRG Development  
**Status:** In Progress (wizard & cron skeleton; provider client pending)

---

## 1. Purpose

Provide automated translation support for OpenEduCat content (currently `op.subject`, extensible to other models) via external translation providers (DeepL, Google Translate) with:
- Daily paginated cron batch processing to manage API cost & load
- Manual wizard interface for on-demand batch translations
- System parameters for provider configuration and API keys
- Translation-safe field declarations for `op.subject.name` and other content fields

## 2. Problem Statement

### Problem
IRG operates a bilingual E-learning platform (Spanish/English) with OpenEduCat courses. Subject names, course descriptions, and other content must be translated to serve students in both languages. Current workflow:
- **Manual translation:** time-consuming, error-prone, inconsistent quality
- **No bulk automation:** individual record edits needed for each language
- **No external provider:** in-house translation lacks speed & quality for large catalogs

### Use Cases
1. **Bulk subject name translation on import:** When new subjects are added to the platform, auto-translate their names (Spanish → English) immediately on create/update
2. **Daily sync cron:** Periodically scan untranslated or updated subjects and batch them to a translation provider
3. **Manual wizard:** Admin can trigger a single batch of translations on demand via a wizard dialog
4. **Cost control:** Paginated batches prevent overwhelming translation API quotas

## 3. Scope

### In Scope
- ✅ Mark `op.subject.name` as `translate=True`
- ✅ Provide skeleton `_translate_record_fields()` method on `op.subject` for future provider integration
- ✅ Create `irg.auto.translate` model with `cron_run()` method for paginated batch processing
- ✅ Create `irg.translate.wizard` transient model with view for manual batch trigger
- ✅ Add system parameters: `irg_auto_translate.provider` (enum: none/deepl/google) and `irg_auto_translate.api_key`
- ✅ Add ir.cron record (disabled by default, set to daily)
- ✅ Add security/ir.model.access.csv for least-privilege access
- ✅ Manifest structure and dependencies

### Out of Scope
- **Provider client implementation:** Skeleton only; provider-specific HTTP clients (DeepL, Google) will be added as a future module (`irg_auto_translate_provider_deepl`, etc.)
- **Translation of other models:** Currently only `op.subject`; extend to `op.course`, `op.batch`, etc. in follow-up modules
- **Webhook or streaming translation:** Only batch processing
- **Translation memory or cache:** No caching of previous translations
- **Multi-language chains:** No transitivity (e.g., Spanish → French via English); only direct source→target translations

## 4. Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  irg_auto_translate Module                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Models:                                                    │
│  ├─ OpSubjectTranslate (_inherit "op.subject")            │
│  │  ├─ name: Char(..., translate=True)                    │
│  │  └─ _translate_record_fields(lang) → Skeleton         │
│  │                                                         │
│  ├─ IrgAutoTranslate (new)                                │
│  │  └─ cron_run() → Paginated batch over op.subject      │
│  │                                                         │
│  └─ IrgTranslateWizard (transient)                        │
│     ├─ model_name, lang_to, batch_size, offset           │
│     └─ action_run() → Single batch trigger               │
│                                                             │
│  Data (XML):                                               │
│  ├─ ir.config_parameter (provider + api_key)            │
│  ├─ ir.cron (daily, disabled by default)               │
│  └─ ir.ui.view (wizard form)                            │
│                                                             │
│  Security:                                                 │
│  └─ ir.model.access (read-only for base.group_user)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Translatable Fields:**
   - `op.subject.name` marked `translate=True` so Odoo's translation engine owns the multilingual storage
   - Future model additions override the field, mark `translate=True`, and inherit `_translate_record_fields()`

2. **Skeleton Hooks:**
   - `_translate_record_fields(lang)` is a **no-op placeholder** on `OpSubjectTranslate`
   - Logs intent to translate but does not call external API (avoids crashes until provider client exists)
   - Future provider modules will override or extend this method

3. **Paginated Cron:**
   - `IrgAutoTranslate.cron_run()` processes subjects in batches of 100 (configurable)
   - Each batch is passed to `_translate_record_fields(lang='es')`
   - Loop continues until all records are processed
   - Failures are logged but do not halt the cron

4. **Wizard for Manual Batching:**
   - Allows admin to select:
     - Target model (`op.subject` currently)
     - Language code (e.g., `es`, `en`)
     - Batch size (default 50)
     - Offset for partial processing (e.g., resume interrupted batches)
   - Single-action form: user clicks "Run", batch is processed, wizard closes

5. **System Parameters (ir.config_parameter):**
   - `irg_auto_translate.provider`: Enum value (default `'none'`)
   - `irg_auto_translate.api_key`: Sensitive string (future modules read this for authentication)

6. **Cron Setup:**
   - Default interval: daily
   - Default state: enabled (can be disabled via Admin > Automation > Scheduled Actions)
   - Safe: runs as root user with no output side effects (only logging + schema updates)

---

## 5. Database / Data Changes

### New Models
| Model               | Type       | Key Fields                    | Purpose                              |
|---------------------|------------|-------------------------------|--------------------------------------|
| `irg.auto.translate`| Regular    | `name`                        | Cron scheduler helper                |
| `irg.translate.wizard` | Transient | `model_name, lang_to, batch_size, offset` | Manual batch trigger       |

### Modified Models
| Model      | Changes                    | Rationale                                 |
|------------|----------------------------|-------------------------------------------|
| `op.subject` | `name` field now `translate=True` | Enable i18n storage for names            |

### New Config Parameters
| Key                           | Value (Default) | Configurable |
|-------------------------------|-----------------|--------------|
| `irg_auto_translate.provider` | `'none'`        | Yes (via Settings UI) |
| `irg_auto_translate.api_key`  | `''` (empty)    | Yes (via Settings UI) |

---

## 6. External Dependencies

### Current (Skeleton Only)
- `base`, `website`, `openeducat_core` (built-in Odoo modules)
- No external Python packages required

### Future (When Provider Client Added)
- `requests` (for HTTP calls to DeepL/Google)
- `deepl` or `google-cloud-translate` (optional language-specific clients)

---

## 7. Implementation Notes

### Model Files

#### `models/op_subject.py`
```python
class OpSubjectTranslate(models.Model):
    _inherit = "op.subject"
    
    name = fields.Char('Name', size=128, required=True, translate=True)
    
    def _translate_record_fields(self, lang):
        """Placeholder for provider integration."""
        for record in self:
            _logger.info("..." % record.id, lang)
        return True
```

#### `models/auto_translate.py`
```python
class IrgAutoTranslate(models.Model):
    _name = "irg.auto.translate"
    
    @api.model
    def cron_run(self):
        """Paginated batch: process subjects in chunks of 100."""
        batch_size = 100
        offset = 0
        while True:
            subjects = self.env['op.subject'].search([], offset=offset, limit=batch_size)
            if not subjects:
                break
            subjects._translate_record_fields(lang='es')
            offset += batch_size
        return True
```

#### `wizard/translate_wizard.py`
```python
class IrgTranslateWizard(models.TransientModel):
    _name = 'irg.translate.wizard'
    
    model_name = fields.Selection([('op.subject', 'Subject')], default='op.subject')
    lang_to = fields.Char(default='es')
    batch_size = fields.Integer(default=50)
    offset = fields.Integer(default=0)
    
    def action_run(self):
        """Run one batch."""
        records = self.env[self.model_name].search([], offset=self.offset, limit=self.batch_size)
        if records:
            records._translate_record_fields(self.lang_to)
        return {'type': 'ir.actions.act_window_close'}
```

### Data Files

#### `data/ir_config_parameter.xml`
Defines two system parameters:
- `irg_auto_translate.provider` (initially `'none'`)
- `irg_auto_translate.api_key` (initially empty)

#### `data/ir_cron.xml`
Defines a daily cron record that calls `IrgAutoTranslate.cron_run()`.

#### `data/ir_ui.view` (in wizard views)
Transient form with model/ language/ batch_size fields and a "Run" button.

---

## 8. Testing Strategy

### Unit Tests (`tests/test_auto_translate.py`)
- **Test 1:** Verify `op.subject.name` is translatable (inspect field definition)
- **Test 2:** Verify `OpSubjectTranslate._translate_record_fields()` returns True and logs
- **Test 3:** Verify `IrgAutoTranslate.cron_run()` completes without error on empty DB
- **Test 4:** Verify `IrgAutoTranslate.cron_run()` processes subjects in correct batch order
- **Test 5:** Verify `IrgTranslateWizard.action_run()` processes specified batch

### Integration Tests (Staging)
- Create 150 subjects in staging DB
- Run cron manually (expects 2 batches of 100+50 iterations logged)
- Trigger wizard manually with offset=50, batch_size=40 (expects 40 records logged)
- Verify no DB errors, exception handling works

### Provider Integration Tests (Future)
- Mock DeepL/Google API responses
- Verify provider client is invoked with correct parameters
- Verify translations are written to ir.translation table with correct lang code

---

## 9. Rollout Plan

### Phase 1 (Current — March 2026)
- ✅ Deploy skeleton module to Dev_iRG branch
- ✅ Module is installable (all syntax valid)
- ✅ Cron/wizard run without errors (no-op behavior)
- ✅ Unit tests pass

### Phase 2 (Q2 2026 — Provider Client)
- Implement `irg_auto_translate_provider_deepl` module with real HTTP calls
- Update `OpSubjectTranslate._translate_record_fields()` to delegate to provider
- Update `irg_auto_translate.provider` system param to default to DeepL
- Add staging API key to environment configuration

### Phase 3 (Q3 2026 — Extend Models)
- Add translation support to `op.course`, `op.batch`, other OpenEduCat entities
- Extend wizard model_name selection
- Implement translation memory caching for cost control

### Phase 4 (Q4 2026 — Production)
- Set cron to enabled on production
- Monitor translation API usage and cost
- Adjust batch sizes, cron frequency based on production load

---

## 10. Changelog

### v16.0.1.0.0 (March 25, 2026) — Initial Skeleton
- **Added:** `OpSubjectTranslate` model with translatable `name` field
- **Added:** `IrgAutoTranslate` model + `cron_run()` for paginated batch processing
- **Added:** `IrgTranslateWizard` transient model + form view for manual triggering
- **Added:** System parameters `irg_auto_translate.provider` and `irg_auto_translate.api_key`
- **Added:** Daily ir.cron record (set disabled by default)
- **Added:** Security CSV with read access for base.group_user
- **Status:** Skeleton; no provider client (placeholder logging only)

---

## Approval & Sign-Off

| Role              | Name    | Date | Status    |
|-------------------|---------|------|-----------|
| Developer         | Agent   | 25-Mar-26 | ✅ Ready  |
| Architecture      | —       | —    | ⏳ Pending |
| Testing (QA)      | —       | —    | ⏳ Pending |
| Product Owner     | —       | —    | ⏳ Pending |

---

## References

- [SPECIFICATIONS.md](../SPECIFICATIONS.md) — Module scaffolding template
- [copilot-instructions.md](../../.github/copilot-instructions.md) — Non-Odoo modification rule
- Odoo 16 Fields & Translate API: https://www.odoo.com/documentation/16.0/
