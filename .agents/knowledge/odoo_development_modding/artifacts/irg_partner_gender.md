# IRG Partner Gender — UI y resolución en matrícula

## Contexto

`res.partner.gender` existía (Moodle / sale / gender_fix) pero solo era usable en la pestaña Moodle. La matrícula automática usaba `sale.order.gender or partner.gender or 'o'` y caía en `'o'`.

## Patrón

Módulo puente `irg_partner_gender`:

1. Vista de contacto: `gender` antes de `category_id`.
2. Vista de pedido: `gender` en pestaña `sale_admission`.
3. `res.partner._irg_resolve_gender(order_gender, write_back)` — cascada y persistencia canónica `m`/`f`/`o`.
4. `sale.order` resuelve género antes de `super()` en create admission.

Clears Moodle `username` required=True on `res.partner` so contact gender can be edited without a Moodle username.
