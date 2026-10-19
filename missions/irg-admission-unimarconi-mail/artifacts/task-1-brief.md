## Test command

Desde la raíz del repositorio, con el runtime local ya levantado:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf \
  -d test_irg_unimarconi_mail \
  -i irg_admission_unimarconi_mail \
  --test-enable \
  --test-tags=/irg_admission_unimarconi_mail \
  --stop-after-init \
  --http-port=8099 \
  --log-level=test
```

En una pasada posterior sobre la misma base, sustituir `-i` por `-u`. La base es desechable. El código de lote de cada test debe caber en 16 caracteres y ser único.

---


### Task 1: Visibility of official-master admissions

**Files:**
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/__init__.py`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/__manifest__.py`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/models/__init__.py`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/models/op_admission.py`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/tests/__init__.py`
- Test: `addons-extra/extrairg/irg_admission_unimarconi_mail/tests/test_unimarconi_mail.py`

**Interfaces:**
- Consumes: `op.admission`, `op.batch.code`, `op.course`, `op.admission.register`.
- Produces: `irg_batch_code_is_official_master(code) -> bool` and `op.admission.irg_show_unimarconi_mail` (Boolean, no almacenado).

- [ ] **Step 1: Write the failing test**

Create the module skeleton so Odoo can install it, with the compute still returning `False`. Then add the test.

`__init__.py`:

```python
from . import models
```

`models/__init__.py`:

```python
from . import op_admission
```

`__manifest__.py`:

```python
{
    'name': 'IRG Admission Unimarconi Mail',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Correo de matrícula Unimarconi en admisiones de máster oficial',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': ['openeducat_admission', 'mail'],
    'data': [],
    'installable': True,
    'application': False,
}
```

`models/op_admission.py` (skeleton, always hidden):

```python
from odoo import api, fields, models


def irg_batch_code_is_official_master(code):
    return False


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    irg_show_unimarconi_mail = fields.Boolean(
        compute='_compute_irg_show_unimarconi_mail',
        string='Mostrar correo Unimarconi',
    )

    @api.depends('batch_id', 'batch_id.code')
    def _compute_irg_show_unimarconi_mail(self):
        for admission in self:
            code = admission.batch_id.code if admission.batch_id else ''
            admission.irg_show_unimarconi_mail = (
                irg_batch_code_is_official_master(code)
            )
```

`tests/__init__.py`:

```python
from . import test_unimarconi_mail
```

`tests/test_unimarconi_mail.py`:

```python
from odoo.tests.common import TransactionCase

from odoo.addons.irg_admission_unimarconi_mail.models.op_admission import (
    irg_batch_code_is_official_master,
)


class TestUnimarconiMailVisibility(TransactionCase):

    def setUp(self):
        super().setUp()
        self.course = self.env['op.course'].create({
            'name': 'Máster en Neuropsicología Clínica',
            'code': 'T-UNI-MAIL',
        })
        product = self.env['product.product'].create({
            'name': 'Producto test Unimarconi',
            'type': 'service',
        })
        self.register = self.env['op.admission.register'].create({
            'name': 'Registro test Unimarconi',
            'course_id': self.course.id,
            'period': '2026-10',
            'start_date': '2026-10-01',
            'end_date': '2026-10-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': product.id,
            'minimum_age_criteria': 3,
        })

    def _batch(self, code):
        return self.env['op.batch'].create({
            'name': code[:32],
            'code': code,
            'course_id': self.course.id,
            'start_date': '2026-10-01',
            'end_date': '2026-12-31',
        })

    def _admission(self, batch_code, email='maria@example.com'):
        batch = self._batch(batch_code) if batch_code else False
        return self.env['op.admission'].create({
            'name': 'María López',
            'first_name': 'María',
            'last_name': 'López',
            'gender': 'f',
            'birth_date': '1990-01-01',
            'email': email,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': batch.id if batch else False,
        })

    def test_prefix_helper(self):
        self.assertTrue(irg_batch_code_is_official_master('MOPCONL2606'))
        self.assertTrue(irg_batch_code_is_official_master('  moabc'))
        self.assertTrue(irg_batch_code_is_official_master('MONLHC2601'))
        self.assertFalse(irg_batch_code_is_official_master('MPTEST01'))
        self.assertFalse(irg_batch_code_is_official_master('MBTEST01'))
        self.assertFalse(irg_batch_code_is_official_master('MIAMONL2601'))
        self.assertFalse(irg_batch_code_is_official_master(''))
        self.assertFalse(irg_batch_code_is_official_master(False))

    def test_button_flag_follows_batch_code(self):
        official = self._admission('MOPCONL2606')
        lowercase = self._admission('moabc2601')
        neurologopedia = self._admission('MONLHC2601')
        propio = self._admission('MPTEST01')
        bonificado = self._admission('MBTEST01')
        other = self._admission('MIAMONL2601')
        empty = self._admission(False)
        self.assertTrue(official.irg_show_unimarconi_mail)
        self.assertTrue(lowercase.irg_show_unimarconi_mail)
        self.assertTrue(neurologopedia.irg_show_unimarconi_mail)
        self.assertFalse(propio.irg_show_unimarconi_mail)
        self.assertFalse(bonificado.irg_show_unimarconi_mail)
        self.assertFalse(other.irg_show_unimarconi_mail)
        self.assertFalse(empty.irg_show_unimarconi_mail)
        self.assertEqual(official.state, 'draft')
        official.state = 'done'
        self.assertTrue(official.irg_show_unimarconi_mail)
```

- [ ] **Step 2: Run the test and confirm it fails**

Run the test command from the header.

Expected: FAIL. `test_prefix_helper` fails because `MOPCONL2606` returns `False`.

- [ ] **Step 3: Implement the prefix**

Replace `irg_batch_code_is_official_master` with:

```python
def irg_batch_code_is_official_master(code):
    return (code or '').strip().upper().startswith('MO')
```

- [ ] **Step 4: Run the test and confirm it passes**

Run the same command with `-u irg_admission_unimarconi_mail` instead of `-i`.

Expected: the two visibility tests PASS.

- [ ] **Step 5: Commit checkpoint**

No ejecutar `git commit` sin autorización explícita del usuario. Si la hay:

```bash
git add addons-extra/extrairg/irg_admission_unimarconi_mail
git commit -m "$(cat <<'EOF'
Add official-master detection for the Unimarconi admission mail.

EOF
)"
```

---

