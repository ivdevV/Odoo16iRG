# Ejecución — cierre de expediente al autocerrar la libreta

## Decisiones

- La plantilla notifica el cierre. No pide generar diploma ni adjunta PDF.
- El cuerpo incluye el correo del alumno, añadido al diseñar la plantilla, para que académica pueda contactarle.
- Commit no autorizado.

## Registro

- Plan escrito antes del código de producción.
- RED: el primer arranque falló en el fixture porque `op.course.lang` es obligatorio. Corregido el fixture con `en_US`. La segunda corrida, sin el hook, dio `3 failed, 0 error(s) of 5 tests`. Fallaron fecha y aviso. Pasaron el cierre manual y la fecha ya existente. Evidencia: `artifacts/tdd-red.txt`.
- El cuerpo con `{{ }}` no se renderiza: `body_html` usa QWeb. El asunto sí, porque es plantilla en línea. El cuerpo pasó a `t-out`. La plantilla ya cargada con `noupdate` se borró en la base de prueba para que `-u` la recreara.
- GREEN: `0 failed, 0 error(s) of 5 tests` en `test_irg_gradebook_expediente_close`. Evidencia: `artifacts/tdd-green.txt`.
- Comando: `docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_gradebook_expediente_close -u irg_gradebook_expediente_close --test-enable --test-tags=/irg_gradebook_expediente_close --max-cron-threads=0 --stop-after-init --http-port=8099 --log-level=test`.
- La base de prueba sigue creada. El contenedor de la corrida se eliminó con `--rm`. El servicio de `8069` no se tocó.
- Review [Review cierre de expediente](4b7c57cd-61a5-4bae-9232-0752eb21d0df): sin críticos. Importante: el envío no tenía savepoint, así que un error SQL deshacía el cierre. Importante: las pruebas corrían como superusuario.
- Corrección: `with self.env.cr.savepoint()` alrededor de `send_mail`. Prueba que ejecuta un SQL inválido y después `SELECT 1`. Prueba con usuario de facultad sin permiso de escritura en el alumno. La libreta manual se prepara lista sin pasar por el autocierre. `isep_gradebook` queda en `depends`.
- RED de esa corrección: `InFailedSqlTransaction` en `test_database_error_while_sending_keeps_close_and_date`.
- GREEN posterior: `0 failed, 0 error(s) of 7 tests`. Evidencia actualizada en `artifacts/tdd-green.txt`.
- Segunda review del mismo revisor: sin críticos ni importantes. Lista para validar.
- Validación independiente: `verification.json` con `status: passed`. Pruebas `0 failed, 0 error(s) of 7 tests`. `e2e_testsprite` skipped por alcance: no hay vistas, portal, website ni controladores.
- Documentación: `README.md` del módulo, `missions/irg-gradebook-expediente-close/CHANGELOG.md`, y el patrón del savepoint en `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_auto_close.md`.
- Título del aviso pasado a `CIERRE DE EXPEDIENTE` en el asunto y en el encabezado del cuerpo. Pruebas otra vez: `0 failed, 0 error(s) of 7 tests`.
- El usuario autorizó subir este alcance a `Dev_iRG`. El commit y el push quedan registrados al hacerlos.
