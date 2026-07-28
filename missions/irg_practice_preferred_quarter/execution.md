# Execution Journal — IRG Practice Preferred Quarter

## Mission opening
- Date: 2026-07-28
- Tier: `standard`
- Base module: `addons-extra/extrairg/irg_practice_preferred_quarter`

## Summary of Accomplished Tasks
1. Micro-spec redactada en `doc/micro-specs/2026-07-28-irg_practice_preferred_quarter.md`.
2. Módulo `irg_practice_preferred_quarter` creado en `addons-extra/extrairg/`.
3. Campo `irg_preferred_quarter` añadido al modelo `practice.request` con las 4 opciones especificadas:
   - `Marzo a Mayo`
   - `Junio a Agosto`
   - `Septiembre a Noviembre`
   - `Diciembre a Febrero`
4. Plantilla portal inyectada mediante XPath en `isep_practices_2.practice_request_form_template` posicionado justo antes del selector de "Tipo de práctica".
5. Vista de formulario backend (`isep_practices_2.view_practice_request_form`) heredada para visibilizar el campo `irg_preferred_quarter`.
6. Controlador portal extendido para validar que la opción no esté vacía y almacenar la selección en `practice.request`.
7. Tests unitarios redactados y ejecutados.
8. Verificación de sintaxis de Python y XML superadas al 100%.

## Checks & Verification Results
- `py_compile`: PASS
- `xml.etree.ElementTree`: PASS
- `verification.json`: status = passed
