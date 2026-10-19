# Plan — cinta roja de dotado en contacto y alumno

`irg_moroso_banner` muestra **Dotado por morosidad** en rojo en el contacto y en el alumno cuando hay al menos una factura de cliente con `irg_dotado_morosidad`. La cinta lila queda oculta mientras la roja está activa. La cinta de la factura no cambia.

Spec: `docs/superpowers/specs/2026-10-19-irg-moroso-banner-dotado-design.md`.

## jev_intake

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 1.0, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.89, "needs_security_advisor": false, "security_noul": 0.2, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```

## Tier

`standard`. El cambio vive en un módulo ya existente, con una regla acotada y las mismas vistas. `needs_security_advisor` es falso. Capacidad usada: la de esta sesión.

## Conocimiento

- `.agents/knowledge/odoo_development_modding/artifacts/odoo_qweb_xpath_parent_shape.md`: la cinta nueva se ancla a la cinta lila ya heredada en cada formulario.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_student_payment_status.md`: no se duplica la nota si el valor no cambia. Ese módulo no se edita.
- `docs/superpowers/specs/2026-10-19-irg-invoice-dotacion-banner-design.md`: la marca de la factura es `account.move.irg_dotado_morosidad`.

## Criterios de aceptación

- Una factura de cliente con `irg_dotado_morosidad` basta, aunque esté pagada.
- Mismo vínculo de contacto que la cinta lila: alumno por `partner_id` o `irg_student_partner_id`; el resto solo por `partner_id`.
- Cinta `bg-danger`, título `Dotado por morosidad`, en contacto y alumno. La lila se oculta si la roja está activa. `irg_is_moroso` no se apaga por ello.
- Notas `Pasa a dotado por morosidad.` y `Deja de estar dotado por morosidad.` solo cuando el booleano cambia y `notify` es verdadero.
- Instalación y migración `16.0.1.1.0` recalculan con `notify=False`.

## E2E

El diff toca vistas de formulario. `e2e_testsprite` es obligatorio. `projectPath`: `addons-extra/extrairg/irg_moroso_banner`.

## Pruebas

`docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local` con `-d test_irg_moroso_banner -u irg_moroso_banner --test-enable --test-tags /irg_moroso_banner --without-demo=all --max-cron-threads=0 --stop-after-init`.

## Publicación

No autorizada.
