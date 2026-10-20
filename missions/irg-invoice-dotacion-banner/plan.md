# Plan — cinta de dotación por morosidad en la factura

Módulo nuevo `irg_invoice_dotacion_banner`. Cinta **Dotado por morosidad** en la factura de cliente cuando uno de sus apuntes está conciliado con un asiento publicado cuya referencia o etiqueta contiene «Dotación por morosidad». La nota del cambio va al historial de la factura. No se modifica `irg_moroso_banner`.

Spec: `docs/superpowers/specs/2026-10-19-irg-invoice-dotacion-banner-design.md`.

## jev_intake

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 1.0, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.95, "needs_security_advisor": false, "security_noul": 0.07, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```

## Tier

`complex`. Módulo nuevo, más de cinco archivos, y la regla cruza facturas, apuntes y conciliaciones. `needs_security_advisor` es falso: no hay autenticación, secretos, borrado histórico, migración ni despliegue. El `sudo()` de la búsqueda y de la nota está acotado en la spec. Capacidad usada: la de esta sesión. El runtime no permite elegir otro modelo.

## Conocimiento

- `.agents/knowledge/odoo_development_modding/artifacts/odoo_qweb_xpath_parent_shape.md`: el xpath se ancla al widget real `web_ribbon` con `text="Invoicing App Legacy"` de `account.view_move_form`.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_student_payment_status.md`: no se duplica la nota si el valor no cambia, y ese módulo no se edita. `irg_moroso_banner` tampoco.

## Criterios de aceptación

- Solo `move_type = out_invoice`. El asiento, el abono y la factura de proveedor quedan en falso.
- La frase `_IRG_DOTACION_PHRASE = 'dotación por morosidad'` se busca sin distinguir mayúsculas y con tilde, en `ref` del otro asiento publicado o en `name` del apunte conciliado.
- Una conciliación parcial cuenta. Varias líneas dejan un solo verdadero y una sola nota.
- Campo `account.move.irg_dotado_morosidad`: booleano almacenado, default falso, `copy=False`, índice, sin `tracking`.
- Recálculo al crear o borrar `account.partial.reconcile`, al cambiar `state` o `ref` del asiento y al cambiar `name` de un apunte.
- Nota `mail.mt_note`: «Pasa a dotado por morosidad.» y «Deja de estar dotado por morosidad.». Solo si el booleano cambia y `notify` es verdadero.
- `post_init_hook` usa el mismo recálculo con `notify=False`. No hay cron.
- Cinta título `Dotado por morosidad`, clase `irg_bg_dotado`, fondo `#4F6D7A`, texto `#FFFFFF`, después de la cinta «Invoicing App Legacy».

## E2E

El diff toca `views/account_move_views.xml`. `e2e_testsprite` es obligatorio. `projectPath`: `addons-extra/extrairg/irg_invoice_dotacion_banner`. Runtime local `docker-compose.local.yml`, puerto 8069, base desechable. No se apunta a beta ni a producción.

## Pruebas de módulo

`docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local` con `-d test_irg_invoice_dotacion -i irg_invoice_dotacion_banner --test-enable --test-tags /irg_invoice_dotacion_banner --without-demo=all --max-cron-threads=0 --stop-after-init`.

## Publicación

No autorizada. No hay commit, push ni PR.
