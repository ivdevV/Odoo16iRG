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

## Nota con la lista

Al pagar una de dos cuotas vencidas la nota no se quedaba en el primer número. Ahora se vuelve a anotar cuando cambia el conjunto, con una línea por cuota: pedido, plazo, vencimiento e importe. Versión `16.0.1.3.0`. La migración llama a `_cron_recompute_moroso()`.

Pruebas: `0 failed, 0 error(s) of 21 tests` el 2026-10-21 en `test_irg_moroso_banner`.

## Publicación

No autorizada. No se ha instalado en la base que sirve el puerto 8069.

## Plazo de pago, 16.0.1.4.0

El cronograma «01 de 01» no es la lista de meses. RED el 2026-10-21: `2 failed, 0 error(s) of 23 tests`. Sin factura el plazo no contaba. Con cobro parcial seguían saliendo las fechas del cronograma.

GREEN con el mismo comando: `0 failed, 0 error(s) of 23 tests`. La cuota es cada línea del plazo desde `start_date`. Lo cobrado se reparte desde el primer mes. El mes en curso queda fuera. Si hay plazo, el cronograma no se suma. La migración `16.0.1.4.0` vuelve a anotar. No se ha ejecutado `-u` en beta: esa migración escribe la nota nueva en los contactos.
