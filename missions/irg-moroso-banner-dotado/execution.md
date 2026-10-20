# Ejecución — cinta roja de dotado

## Decisiones

- Se modifica `irg_moroso_banner`, que es el módulo que el usuario pidió cambiar.
- Pasa a depender de `irg_invoice_dotacion_banner` para leer `irg_dotado_morosidad`.
- Tier `standard`. Sin Security Advisor.
- Publicación no autorizada.

## TDD

- RED: `1 failed, 8 error(s) of 24 tests`. Faltaba `irg_is_dotado_morosidad` y la cinta roja. Evidencia: `artifacts/tdd-red.txt`.
- GREEN: `0 failed, 0 error(s) of 24 tests` en `test_irg_moroso_banner`, 2026-10-19 14:01:17. Evidencia: `artifacts/tdd-green.txt`.
- `python3 -m compileall` del módulo: correcto.

## Review

Revisor [Review red moroso ribbon](13e8e159-f527-4b34-9838-39812e33d876): aprobado, sin hallazgos bloqueantes. La cinta lila se oculta cuando la roja está activa, una factura pagada y dotada marca al contacto, y la instalación no publica la nota de dotado.

## Pendiente

`e2e_testsprite` no se ha ejecutado. El diff toca las vistas de contacto y alumno. No hay `verification.json`.

El usuario autorizó commit y push a `Dev_iRG`.
