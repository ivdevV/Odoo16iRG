# Plan — cierre de expediente al autocerrar la libreta

Módulo nuevo `irg_gradebook_expediente_close`. Al terminar el autocierre, si el alumno no tiene fecha de cierre de expediente, escribe la de hoy y avisa a `academica@institutoraimongaja.com`. No se edita `irg_gradebook_auto_close` ni `isep_student_filter`.

Spec: `docs/superpowers/specs/2026-10-19-irg-gradebook-expediente-close-design.md`.

## jev_intake

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 1.0, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.91, "needs_security_advisor": false, "security_noul": 0.11, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```

## Tier

`complex`. Módulo nuevo, más de cinco archivos, cruza libreta, alumno y correo. `needs_security_advisor` es falso. El `sudo()` de la fecha y del envío está acotado en la spec. Capacidad usada: la de esta sesión. El runtime no permite elegir otro modelo.

## Conocimiento

- `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_auto_close.md`: el cierre pasa por `_irg_try_auto_close()` y `state_to_done()`. Un fallo derivado no debe deshacer la mutación principal. No hay barrido al instalar.
- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`: el aviso usa `mail.template` nativo, sin heredar `mail.mail`.

## Criterios de aceptación

- Solo el autocierre. `state_to_done()` directo no escribe la fecha ni envía correo.
- `op.student.file_closing_date` se rellena con `fields.Date.context_today(gradebook)` solo si está vacía.
- El correo sale solo en ese caso, a `academica@institutoraimongaja.com`, con la plantilla de la spec.
- Dos libretas del mismo alumno en la misma llamada: una fecha y un correo.
- Si `send_mail` falla, la libreta sigue en `done`, la fecha se conserva y la excepción no sale.
- No hay barrido de libretas ya finalizadas.

## Plantilla

`irg_gradebook_expediente_close.mail_template_expediente_close`. Asunto `Cierre de expediente: <alumno> — <admisión> — <curso>`. Cuerpo con alumno, correo del alumno, curso, admisión, libreta y fecha `dd/MM/yyyy`. Remitente `Instituto Raimon Gaja <academica@institutoraimongaja.com>`. El código fuerza `email_to` en `email_values`.

## E2E

El diff no toca vistas, QWeb de `views/`, `templates/` o `report/`, assets, portal, website ni controladores. `e2e_testsprite` queda `skipped`.

## Pruebas de módulo

`docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local` con `-d test_irg_gradebook_expediente_close -i irg_gradebook_expediente_close --test-enable --test-tags /irg_gradebook_expediente_close --without-demo=all --max-cron-threads=0 --stop-after-init`.

## Publicación

No autorizada. No hay commit, push ni PR.
