# Execution — irg-campus-certificates-tile-qweb-fix

## Decisiones

- Inherit-only. No se toca `irg_campus_certificates_portal`.
- Guard QWeb: `not course_id.is_diplomado()` (mismo helper que Prácticas/TFM).
- `auto_install: True` si están instalados certificados + diplomado_hide.

## Knowledge citada

- `modding_rules_and_email_analysis.md`
- `irg_diplomado_portal_request.md`
- `irg_course_portal_tiles_diplomado_hide.md`

## RED

Esqueleto del módulo sin vista. 1 failed + 2 error(s) of 3 tests.

- `test_combined_t_if_does_not_use_hasattr`: `hasattr` sigue en el `t-if`.
- render máster y diplomado: `TypeError: 'NoneType' object is not callable` (el mismo de beta).

Evidencia: `artifacts/red-tests.txt`.

## GREEN

Vista inherit `views/campus_dashboard_override.xml`. 0 failed, 0 error(s) of 3 tests.

Evidencia: `artifacts/green-tests.txt`.

## Review

REVIEW PASS. Informe: `02b-review.md`.

## Validación

Tests de módulo PASS. E2E TestSprite FAIL (MCP no disponible en la sesión).
`verification.json` queda `failed` por ese gate. El arreglo de QWeb está
cubierto por los 3 tests de módulo que reproducen el TypeError de beta.


