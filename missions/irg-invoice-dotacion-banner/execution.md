# Ejecución — cinta de dotación por morosidad

## Decisiones

- Módulo nuevo. No se edita `irg_moroso_banner`.
- Tier `complex`. Sin Security Advisor: Jev devolvió `needs_security_advisor` falso y el cambio no toca autenticación, secretos, migración ni borrado histórico.
- Publicación no autorizada.

## TDD

- RED: `2 failed, 15 error(s) of 17 tests`. Faltaban `irg_dotado_morosidad` y la cinta. Evidencia: `artifacts/tdd-red.txt`.
- El xpath por `@text` lo rechaza Odoo porque el atributo es traducible. La cinta queda detrás de `//sheet/widget[@name='web_ribbon'][last()]`, la última de `account.view_move_form`.
- Las pruebas van con `@tagged('post_install', '-at_install')`. En `at_install` el módulo carga antes que `account_asset` y la columna `create_asset` ya es obligatoria.
- GREEN: `0 failed, 0 error(s) of 17 tests` en `test_irg_invoice_dotacion`, 2026-10-19 12:14:25. Evidencia: `artifacts/tdd-green.txt`.
- `python3 -m compileall` del módulo: correcto.

## Review

Revisor [Review dotación banner](808d94fa-a404-4850-991a-30a3d5bf7712): aprobado, sin hallazgos bloqueantes. No bloqueantes que se dejan fuera de este cambio: el campo no es `readonly`, el `write` de `state` busca conciliaciones también en facturas recién publicadas, la instalación repite la búsqueda, el test de la vista no afirma el orden de la cinta, y no hay prueba de un usuario portal.

## Pendiente

`e2e_testsprite` no se ha ejecutado. El diff toca `views/account_move_views.xml`, así que sigue siendo obligatorio antes de cerrar la misión. No hay `verification.json`. El módulo no está instalado en la base que sirve el puerto 8069.

El usuario autorizó commit y push a `Dev_iRG`.
