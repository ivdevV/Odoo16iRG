# Spec: fix-admission-gender-detection

## Problema

Al confirmar un pedido de venta (`sale.order.action_confirm`, con o sin el wizard
manual de `irg_sale_manual_confirmation_wizard`), la cadena de autoadmisión crea
`op.admission` / `op.student` con:

```python
'gender': self.gender or target_partner.gender or 'o'
```

Fallas verificadas en código:

1. **Prioridad invertida**: `self.gender` (género del pedido = pagador/titular)
   pisa el del estudiante real (`student_id`). Caso pagador ≠ estudiante → género mal.
2. **Valores Moodle sin mapear**: `odoo_moodle_connector` guarda en
   `res.partner.gender` los valores `'male'/'female'/'not-sure'`; `op.admission` y
   `op.student` esperan `'m'/'f'/'o'`. Los módulos de venta pasan el valor crudo;
   solo lo salva `irg_admission_gender_fix` si está instalado.
3. **Sin dependencia garantizada**: ningún módulo de la cadena de admisión depende
   de `irg_admission_gender_fix` (solo `irg_nlex_grade_exemption`).
4. **"Otro" explícito imposible**: `irg_admission_gender_fix.create()` trata `'o'`
   entrante como "no informado" y lo sobreescribe adivinando por nombre/título.

## Requisitos (decisión del usuario)

- R1. Prioridad de detección: género del **estudiante** (`target_partner` /
  `student_id`) primero; género del pedido solo como fallback.
- R2. Mapeo `'male'/'female'/'not-sure'` → `'m'/'f'/'o'` hecho directamente en los
  módulos de venta (helper compartido), sin depender de que el fix intercepte.
- R3. Respetar `'o'` explícito: el fix no debe sobreescribir `'o'` cuando viene
  informado; solo adivinar cuando el género llega vacío/False.
- R4. Añadir `irg_admission_gender_fix` como dependencia de los módulos de
  admisión (`isep_sale_order_admissions`, `isep_admission_from_student_field`),
  rompiendo antes el ciclo (quitar `isep_admission_from_student_field` de los
  depends del fix; no referencia nada suyo).
- R4b. Quitar TAMBIÉN `odoo_moodle_connector` de los depends de
  `irg_admission_gender_fix`: en producción NO se usa Moodle y no debe venir
  arrastrado transitivamente. El mapeo `'male'/'female'/'not-sure'` se mantiene
  en el código como red de seguridad para datos legacy, pero sin exigir el
  módulo. Depends finales del fix: `openeducat_admission`, `openeducat_core`,
  `isep_openeducat_sale`.

## Puntos de código afectados

- `addons-extra/addons_uisep/isep_openeducat_sale/models/sale_order.py`
  (definir helper `_irg_resolve_admission_gender()`; usarlo en línea ~336).
- `addons-extra/addons_uisep/isep_sale_order_admissions/models/sale_order.py`
  líneas 124 y 273.
- `addons-extra/addons_uisep/isep_admission_from_student_field/models/sale_order.py`
  líneas 106, 127, 157, 222.
- `addons-extra/extrairg/irg_admission_gender_fix/models/op_admission.py` y
  `op_student.py` (`create()`/`write()`).
- Manifests de los tres módulos implicados.
- `addons-extra/extrairg/irg_admission_gender_fix/tests/test_gender_mapping.py`.

## Helper de referencia (diseño aprobado)

```python
_IRG_GENDER_MAP = {'m': 'm', 'f': 'f', 'o': 'o',
                   'male': 'm', 'female': 'f', 'not-sure': 'o'}

def _irg_resolve_admission_gender(self, partner=None):
    """Estudiante primero, pedido como fallback. False si no resoluble."""
    partner = partner or self.partner_id
    raw = (partner and partner.gender) or self.gender
    return self._IRG_GENDER_MAP.get(raw, False)
```

Cuando devuelve `False`, `irg_admission_gender_fix.create()` adivina por
nombre/título (`_map_partner_gender`/`_guess_gender`, lógica existente) y cae a
`'o'` como último recurso.

## Criterios de aceptación globales

- A1. Tests de `irg_admission_gender_fix` (existentes + nuevos) en verde sobre
  `test_irg_db` (contenedor `odoo16irg_local`).
- A2. Nuevo test: pedido con `gender='m'` (pagador) y estudiante con
  `gender='f'` → admisión creada con `'f'`.
- A3. Nuevo test: `'o'` explícito en create/write de `op.admission` no se
  sobreescribe.
- A4. Partner con valor Moodle `'female'` → admisión con `'f'` sin necesidad de
  la intercepción del fix (mapeo en helper).
- A5. Los módulos actualizan sin error de dependencias circulares
  (`-u` de los cuatro módulos en `test_irg_db`).

## Entorno

- Local Docker: contenedores `odoo16irg_local` (Odoo) y `pgodoo16irg_local`
  (Postgres). BD de pruebas: `test_irg_db` (tiene toda la cadena instalada).
- No tocar BD del servidor beta/prod.

## Git

- Rama: `fix/admission-gender-detection` creada desde `Dev_iRG` (regla del repo:
  nunca desde `main`).
