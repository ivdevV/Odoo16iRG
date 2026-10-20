# Ejecución: moroso por cuotas

## RED

`docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_moroso_banner -u irg_moroso_banner --test-enable --test-tags /irg_moroso_banner --without-demo=all --max-cron-threads=0 --stop-after-init --log-level=test`

Resultado con la regla antigua: `11 failed, 0 error(s) of 19 tests`. Dos facturas seguían marcando moroso. Una cuota vencida no marcaba.

La primera corrida falló en `setUpClass` porque `isep_openeducat_sale` exige `course_type` en el producto. El alta de prueba ahora usa `course_type: none`. Esa dependencia se instaló en `test_irg_moroso_banner` al actualizar el módulo.

## GREEN

Mismo comando, tras la regla de cuotas. `0 failed, 0 error(s) of 20 tests` el 2026-10-20. `python3 -m compileall` del módulo sin errores. Resumen en `artifacts/tdd-green.txt`.

El cobro real de la factura vinculada a la cuota también quita la cinta. Lo cubre `test_paying_linked_invoice_clears_flag`.

## Decisiones

- La nota solo se escribe cuando `irg_is_moroso` cambia. Dos cuotas escriben «Cuotas vencidas: 2.» cuando el pedido pasa a confirmado con las dos ya creadas.
- `payment_state` de la cuota es calculado y no llama a `write`. El gancho de la factura lee ese estado antes de buscar, para que el cobro actualice la cinta.
- La migración `16.0.1.2.0` llama a `_cron_recompute_moroso()` con nota. La cinta roja no cambia.

## Publicación

No autorizada. No se ha instalado en la base que sirve el puerto 8069.
