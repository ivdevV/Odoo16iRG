### Task 4: Module readme

**Files:**
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/README.md`

**Interfaces:**
- Consumes: the finished module behavior.
- Produces: the usage note the documenter can extend after validation.

- [ ] **Step 1: Write the readme**

```markdown
# irg_admission_unimarconi_mail

Botón **Enviar matrícula Unimarconi** en la ficha de `op.admission`.

Aparece cuando el código del lote, sin espacios iniciales y en mayúsculas,
empieza por `MO`. Abre el compositor de Odoo con la plantilla
`Admisión: matrícula Unimarconi`. El botón del correo abre
https://oficialidad.institutoraimongaja.com.

El formulario cumplimentado no se guarda en este módulo. La aplicación de
oficialidad lo envía y `irg_student_oficialidad_webhook` lo archiva como
`matricula-unimarconi`.

## Dependencias

`openeducat_admission`, `mail`.

## Pruebas

    docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
      -c /etc/odoo/odoo.conf -d test_irg_unimarconi_mail \
      -u irg_admission_unimarconi_mail --test-enable \
      --test-tags=/irg_admission_unimarconi_mail --stop-after-init \
      --http-port=8099 --log-level=test
```

- [ ] **Step 2: Confirm the module tree**

```bash
find addons-extra/extrairg/irg_admission_unimarconi_mail -type f | sort
```

Expected paths: `__init__.py`, `__manifest__.py`, `README.md`, `models/__init__.py`, `models/op_admission.py`, `views/op_admission_views.xml`, `data/mail_template_data.xml`, `static/src/img/logo-irg.jpg`, `tests/__init__.py`, `tests/test_unimarconi_mail.py`.

No files outside this directory. `git diff --stat` does not list `irg_student_oficialidad_documents` nor `irg_student_oficialidad_webhook`.

- [ ] **Step 3: Commit checkpoint**

No ejecutar sin autorización del usuario.

---

