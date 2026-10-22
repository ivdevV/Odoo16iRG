# Plan — aviso de cierre en botón, barra de estado y API

El módulo `irg_gradebook_expediente_close` solo actúa dentro de `_irg_try_auto_close()`. El botón `state_to_done()`, la barra de estado y un `write({'state': 'done'})` de la API dejan la libreta en Finalizado sin fecha y sin correo. El cambio se hace en ese mismo módulo: el efecto pasa a cualquier `write` que lleve el estado a `done`.

## jev_intake

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 1.0, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.71, "needs_security_advisor": false, "security_noul": 0.08, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```

## Tier

`standard`. Dos archivos de comportamiento, lógica localizada y contexto ya cerrado. `needs_security_advisor` es falso. Capacidad usada: la de esta sesión. El runtime no permite elegir otro modelo.

## Conocimiento

- `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_auto_close.md`: el autocierre termina en `state_to_done()`, que asigna `state = 'done'` y por tanto entra en `write`. Un fallo del correo no debe deshacer el cierre. La fecha se escribe antes del savepoint del envío.
- No se toca `isep_gradebook` ni `irg_gradebook_auto_close`. Otros `write` de `app.gradebook.student` (`irg_tfm_convocatorias`, `irg_admission_auto_gradebook_templates`, `irg_diploma_gradebook_template_authoritative`) siguen en la cadena porque este `write` llama a `super()`.

## Criterios de aceptación

- Cualquier paso ORM a `done` escribe la fecha si está vacía y envía el correo una sola vez. Cubre el autocierre, `state_to_done()`, la barra de estado y `write({'state': 'done'})`.
- La fecha existente no se pisa y no genera correo.
- Dos libretas del mismo alumno, en una sola llamada o en dos, dejan una fecha y un correo.
- Reabrir y volver a finalizar no envía un segundo correo.
- Si el envío falla, la libreta sigue en `done`, la fecha se conserva y la excepción no sale.
- No hay barrido de libretas ya finalizadas. Un `create` que nazca en `done`, o un `UPDATE` SQL, no dispara el aviso.
- El destinatario sigue forzado a `academica@institutoraimongaja.com`.

## E2E

El diff no toca vistas, QWeb de `views/`, `templates/` o `report/`, assets, portal, website ni controladores. `e2e_testsprite` queda `skipped`.

## Pruebas de módulo

`docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_gradebook_expediente_close -u irg_gradebook_expediente_close --test-enable --test-tags=/irg_gradebook_expediente_close --max-cron-threads=0 --stop-after-init --http-port=8099 --log-level=test`

## Publicación

No autorizada. No hay commit, push ni PR.
