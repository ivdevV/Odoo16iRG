# Plan: moroso por cuotas de meses cerrados

## jev_intake

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 1.0, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.87, "needs_security_advisor": false, "security_noul": 0.08, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```

## Clasificación

Misión completa. Tier `standard`: un módulo existente, regla acotada, dependencia nueva y migración que reclasifica. Sin Security Advisor.

## Alcance

Spec: `docs/superpowers/specs/2026-10-19-irg-moroso-cuotas-design.md`.

`irg_is_moroso` pasa a ser verdadero con al menos una cuota de `sale.subscription.schedule` sin pagar o parcial, con `date_due` anterior al día 1 del mes en curso y pedido en `sale` o `done`. El alumno cuenta pedidos donde es `student_id` o `partner_id`. Quien no es alumno, solo donde es `partner_id`. La nota dice «Cuotas vencidas: N.». La cinta roja no cambia.

Versión `16.0.1.2.0`. Dependencias nuevas: `isep_sale_subscription_custom`, `irg_sale_order_extended`.

## e2e_testsprite

`skipped`. El diff no toca vistas, assets, portal ni controladores.

## Publicación

No autorizada.

## Pruebas

Sustituir en `tests/test_moroso_banner.py` las que contaban facturas. RED en `test_irg_moroso_banner` antes del cambio de regla. GREEN con `-u irg_moroso_banner --test-tags /irg_moroso_banner`.
