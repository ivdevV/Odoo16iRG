# Plan — cinta de moroso en contacto y alumno

Módulo nuevo `irg_moroso_banner`. Cinta lila **Moroso** en el contacto y en el alumno cuando hay 2 o más facturas de cliente publicadas, impagadas o parciales. La nota del cambio va al historial. No se modifica `irg_student_payment_status`.

Spec: `docs/superpowers/specs/2026-10-19-irg-moroso-banner-design.md`.

## jev_intake

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 0.99, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.96, "needs_security_advisor": false, "security_noul": 0.09, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```

## Tier

`complex`. Módulo nuevo, más de cinco archivos, cruza contactos, facturas y OpenEduCat, y tiene cron. `needs_security_advisor` es falso: no hay autenticación, secretos, borrado histórico ni migración. El `sudo()` de la cuenta de facturas y de la nota está acotado en la spec. Capacidad usada: la de esta sesión. El runtime no permite elegir otro modelo.

## Conocimiento

- `.agents/knowledge/odoo_development_modding/artifacts/student_partner_delegated_fields.md`: el booleano vive solo en `res.partner` porque `op.student` delega con `_inherits`. Las dos vistas se heredan aparte.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_student_payment_status.md`: la deuda se lee de `account.move`; la nota no debe duplicarse si el estado no cambia. Ese módulo no se edita.
- `.agents/knowledge/odoo_development_modding/artifacts/odoo_qweb_xpath_parent_shape.md`: el xpath se ancla a la cinta de archivado real de cada formulario.

## Criterios de aceptación

- Contacto alumno: cuentan facturas con `partner_id` o `irg_student_partner_id` igual a ese contacto.
- Contacto que no es alumno: solo `partner_id`.
- Umbral 2. Estados `not_paid` y `partial`. Excluidos borrador, rectificativa, `in_payment`, pagada y cancelada.
- Cinta `web_ribbon` título Moroso, clase `irg_bg_moroso` (`#7C5CBF` / `#FFFFFF`), solo si `irg_is_moroso`. También si el registro está archivado.
- Nota `mail.mt_note` en el contacto y en cada alumno de ese contacto, solo cuando el booleano cambia.
- Recálculo en create/unlink de `account.move`, en write de `state`, `payment_state`, `partner_id`, `move_type` o `irg_student_partner_id`, y al crear un alumno o cambiar su `partner_id`.
- Cron diario **Recalcular morosos**, `noupdate="1"`, y el mismo cálculo en `post_init_hook`.
- Método extensible `_irg_partner_should_be_moroso`.

## E2E

El diff toca `views/*.xml` de formularios backend. `e2e_testsprite` es obligatorio. `projectPath`: `addons-extra/extrairg/irg_moroso_banner`. Runtime local `docker-compose.local.yml`, puerto 8069, base desechable. No se apunta a beta ni a producción.

## Pruebas de módulo

`docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local` con `-d test_irg_moroso_banner -i irg_moroso_banner --test-enable --test-tags /irg_moroso_banner --without-demo=all --max-cron-threads=0 --stop-after-init`.

## Publicación

No autorizada. No hay commit, push ni PR.
