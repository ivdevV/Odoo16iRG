# Knowledge Base: Odoo Many2one Helpers and Test Dependency Load Order

## Gotcha 1: Many2one Helper Methods and Empty Recordsets
Helper methods on models (e.g. `irg_is_grade_exempt` on `op.subject`) that contain `self.ensure_one()` can cause critical crashes in the UI (like `ValueError: Expected singleton: op.subject()`) when they are called from loops or templates on Many2one fields that are empty or not set.

### Solution Pattern
Helper methods must check if `self` is empty and exit early with a safe default value (usually `False` or `None`) before calling `self.ensure_one()`:
```python
def irg_is_grade_exempt(self):
    if not self:
        return False
    self.ensure_one()
    return bool(self.code and 'EX' in self.code.upper())
```

---

## Gotcha 2: Test Suite Initialization Conflicts and Manifest Dependencies
When running tests with `--test-enable`, Odoo only loads the targeted module and its declared dependencies. If other installed modules in the database modify core selections (such as `res.partner.gender`) and set default values, but the targeted module's test setup creates those records without importing the corrective override module (like `irg_admission_gender_fix`), registry selection mismatch will raise a `ValueError` during test setup (e.g., `Wrong value for res.partner.gender: 'male'`).

### Solution Pattern
Always declare corrective override modules as explicit dependencies in the module's `__manifest__.py` if the test suite creates records affected by those overrides, ensuring correct topological load order:
```python
    'depends': [
        # ...
        'irg_admission_gender_fix',
    ],
```
