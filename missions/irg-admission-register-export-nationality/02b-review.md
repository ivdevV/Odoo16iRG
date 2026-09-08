# Review — irg-admission-register-export-nationality

Alcance revisado: wizard `_COLUMNS`, manifiesto, tests. No se revisan plan/execution/changelog/docs.

## Hallazgos

Ninguno BLOQUEANTE.

### MENOR

- `addons-extra/extrairg/irg_admission_register_export/tests/test_admission_export.py`: las pruebas comprueban que `Nacionalidad` existe y va al final, pero no congelan las 10 etiquetas previas. El código no las altera; un `assertEqual` de cabeceras previas reforzaría el criterio de no reordenar.

### NIT

- `wizard/admission_export_wizard.py`: la lambda usa `a.student_id.nationality.name or ''` (vacío de Odoo → `False` → `''`) en lugar del `if record else ''` de Curso/Lote. Coincide con el plan y es seguro en el new API.
- Las pruebas llaman a `_get_rows` y no a `_build_csv`/`_build_xlsx`. Aceptable: ambos builders recorren esa lista.

## Cumplimiento del plan

- Columna `(_('Nacionalidad'), lambda a: a.student_id.nationality.name or '')` tras Estado.
- Fuente `op.student.nationality` (`res.country`); no `citizenship_country_id` ni `partner.country_id`.
- CSV/XLSX siguen compartiendo `_get_rows`.
- Versión `16.0.1.1.0`. XML, seguridad y dependencias sin cambios funcionales.

REVIEW OK
