# Review — misión fix-admission-gender-detection

(Contenido generado por el subagente Reviewer; persistido por el orquestador
porque el Reviewer solo dispone de herramientas de lectura.)

Nota de entorno: NO existe `PROJECT.md` en el repo (el protocolo SDD lo
referencia pero no se ha ejecutado `/init-sdd`); la revisión se apoya en
`00-spec.md`, `01-plan.md` y la memoria del repo (no tocar BD beta/prod,
trabajar desde `Dev_iRG`).

## Hallazgos

### MAYOR-1 — Octava ocurrencia del patrón buggy sin corregir en `irg_admissions_by_student`
Archivo: `addons-extra/extrairg/irg_admissions_by_student/models/sale_order.py:48`
Sigue con la expresión antigua:
```python
'gender': self.gender or target_partner.gender or 'o',
```
Este módulo hace `_inherit='sale.order'` y define `get_admision_id` (override
total, sin `super()`), creando `op.admission` directamente. Consecuencias:
- Viola R1 (prioridad invertida: `self.gender` del pedido pisa
  `target_partner.gender` del alumno).
- No usa el helper (R2) y su manifest NO depende de `irg_admission_gender_fix`.

Atenuantes que lo dejan en MAYOR y no BLOQUEANTE: (a) fuera del alcance
declarado del plan; (b) en `scratch/modules_availability.json` figura
`local_state: uninstalled`; (c) `isep_sale_order_admissions` neutraliza
`get_admision_id` devolviendo `False`, y en `test_irg_db` la cadena activa pasa
por `_create_or_get_admission`/`create_admission_manual` (ya corregidos);
(d) mientras `irg_admission_gender_fix` esté instalado, su intercepción global
de `op.admission.create` mapea aún los valores Moodle, quedando solo la
prioridad R1 mal.

Corrección recomendada: sustituir la línea 48 por
`self._irg_resolve_admission_gender(target_partner) or 'o'` y añadir
`irg_admission_gender_fix` a los `depends` de su manifest.

### MENOR-1 — `write()` del fix propaga `gender=False` a `super()` si llegara explícito
Archivos: `irg_admission_gender_fix/models/op_admission.py:137-154` y
`op_student.py:137-154`. En `write({'gender': False})`: `incoming_gender` falsy
→ no entra al `if`; el `elif` exige `'gender' not in vals`, que no se cumple →
`False` pasa a `super().write()` y, siendo `gender` `required=True`,
reventaría. Ningún llamador de la cadena escribe `gender=False` (todos usan
`helper(...) or 'o'`), así que no se dispara hoy. Endurecimiento opcional.

### MENOR-2 — Valor de partner mapeable-a-desconocido no dispara adivinación
`isep_openeducat_sale/models/sale_order.py:25-35`. Si `partner.gender` tuviera
un valor truthy fuera de `_IRG_GENDER_MAP`, el helper devuelve `False`, el
llamador aplica `or 'o'` y el fix ya no adivina. Con los valores actuales del
selection no ocurre; nota de robustez futura.

### NIT-1 — Falta `PROJECT.md`
No bloquea; conviene generarlo (`/init-sdd`) para futuras misiones.

### NIT-2 — Warning preexistente de selection en `res.partner`
`irg_admission_gender_fix/models/res_partner.py:12` redefine `gender` con
`fields.Selection([...])` en vez de `selection_add` (warning de override).
Preexistente; correcto no tocarlo en esta misión.

## Verificación de los puntos del encargo

1. Helper `_irg_resolve_admission_gender` (`isep_openeducat_sale/models/sale_order.py:20-35`):
   prioridad partner→pedido correcta, mapeo `_IRG_GENDER_MAP` correcto,
   devuelve `False` si no mapeable. Sin efectos colaterales. OK.
2. Las 7 sustituciones verificadas por lectura. `isep_admission_from_student_field`
   pasa `target_partner` en las 4 (106, 127, 157, 222) — R1 respetado.
   `isep_sale_order_admissions` usa `partner` (124) y `self.partner_id` (273).
   `isep_openeducat_sale` usa `self.partner_id` (336). Ningún patrón antiguo en
   estos 3 archivos. `helper(...) or 'o'` garantiza que nunca llega `False` a
   `op.admission.create` (required). OK.
3. `op_admission.py`/`op_student.py`: `'o'` explícito respetado en `create()` y
   `write()`; mapeo `male/female/not-sure`→`m/f/o` intacto; fallback final a
   `'o'` intacto; sin regresión para gender ausente. OK.
4. Manifests: fix depende de `[openeducat_admission, openeducat_core,
   isep_openeducat_sale]` (R4b); los dos módulos de admisión añaden
   `irg_admission_gender_fix`. Sin ciclo. `res_partner.py` autocontenido:
   quitar `odoo_moodle_connector` no rompe el mapeo legacy. OK.
5. Tests: `test_06` (A2), `test_07` (A3), `test_08` (A4) cubren sus criterios.
   Ajuste de `test_02` justificado tras R3 (no enmascara regresión). Fix de
   fechas del fixture: bug preexistente de robustez temporal, no relacionado
   con género. OK.
6. Riesgos: la intercepción del fix es a nivel de modelo, cubre todo path de
   create una vez instalado; los nuevos `depends` garantizan su instalación.
   Único path sin garantía: `irg_admissions_by_student` (MAYOR-1, hoy
   desinstalado). `write(gender=False)` (MENOR-1) no se dispara desde la cadena.

## Nota para el Validator

Evidencia de A1–A5 pendiente de ejecución real (update de 4 módulos sin ciclo
+ suite `--test-tags irg_gender` sobre `test_irg_db` en `odoo16irg_local`).
`02-progress.md` reporta `0 failed, 0 error(s) of 8 tests` pero requiere
confirmación independiente.

## Veredicto

Sin hallazgos BLOQUEANTES. Cambios en scope satisfacen R1–R4b; A1–A5 cubiertos
por diseño y tests (pendiente ejecución del Validator). MAYOR-1 es remanente
latente fuera de alcance, recomendado abordar.

**REVIEW OK**

---
Adenda del orquestador: MAYOR-1 NO se aplica por decisión del usuario —
`irg_admissions_by_student` no se usa en producción (desinstalado también en
local). Queda documentado aquí como deuda latente: si algún día se reinstala,
aplicar la corrección recomendada (helper + depend de irg_admission_gender_fix).
