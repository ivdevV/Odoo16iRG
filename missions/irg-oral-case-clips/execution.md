# Ejecución — Caso clínico por clips

## Decisiones

- 2026-10-23. Misión `full`, tier `complex`. Rama `cursor/oral-case-clips-8297` desde `Dev_iRG` (`acb64787a`, merge de la PR #52).
- El plan está en `plan.md` y precede a cualquier cambio de producto.
- La skill que pide un módulo nuevo cede: el usuario fijó el módulo `irg_oral_case`. No se editan otros módulos.
- Los Many2one de la libreta y del adjunto solo se escriben con `env.su`. Un flag de contexto no autoriza, porque el RPC puede enviarlo.
- El test `assertRaises((AccessError, MissingError))` se reescribe sin tupla. Sigue exigiendo `AccessError` o `MissingError`.
- `isep_survey.compute_slide_channel_partner` no admite un recordset. Guardar la nota hace flush y, con dos participaciones pendientes, lanzaba `ValueError`. `irg_oral_case` lo hereda y lo ejecuta registro a registro, con la misma búsqueda. No se edita `isep_survey`.
- La ruta de media lee el adjunto en sudo solo después de que la ir.rule deja ver la entrega, y solo sirve el fichero si `res_model`, `res_id`, MIME `video/webm` y `public` es falso. El portal no tiene ACL de lectura sobre adjuntos ajenos; sin ese sudo el vídeo propio respondía 403.

## TDD

El RED no quedó registrado antes de que existiera el código de producto. La primera ejecución de la suite, con ese código ya escrito, es la evidencia de fallo: 3 failed y 4 error de 37 tests (`artifacts/odoo-tests.log`). Causas: frase de consentimiento en el JS, nota del chatter sin decimal, `ValueError` de singleton en el cálculo heredado, y 403 al servir el webm propio. Tras el cambio mínimo, la segunda ejecución quedó en verde (`artifacts/odoo-tests-2.log`).

## Security Advisor

Primera revisión: `[NO]`. El create del portal podía plantar `video_attachment_id` y `user_input_id`, y la ruta de media y el cron se fiaban de ese puntero. El plan incorpora create y write solo con `env.su`, ACL del clip, comprobación de `res_model`/`res_id`/MIME en la ruta y en el cron, nota atada a la alumna, sudo del estado n8n limitado a la sugerencia, y URL con `urlsplit`. Segunda revisión: `[YES]`. Evidencia en `artifacts/security-advisor.txt`.

## Comandos

Runtime local de la PR #53, sin copiar esos ficheros a la rama. Postgres `pgodoo16irg_local`. Base desechable `test_irg_oral_case_clips_8297`.

```
sudo docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_oral_case_clips_8297 -i irg_oral_case --test-enable --test-tags=/irg_oral_case --stop-after-init --workers=0 --http-port=8099 --log-level=test
```

Resultado: EXIT 1. 3 failed, 4 error(s) of 37 tests. Log: `artifacts/odoo-tests.log`.

```
sudo docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_oral_case_clips_8297 -u irg_oral_case --test-enable --test-tags=/irg_oral_case --stop-after-init --workers=0 --http-port=8099 --log-level=test
```

Resultado: EXIT 0. 0 failed, 0 error(s) of 37 tests. Log: `artifacts/odoo-tests-2.log`.

Después de ese verde se sustituyó `invalidate_cache()` por `invalidate_recordset()` en tres tests.

La revisión de código devolvió dos bloqueantes. La corrección de una nota ya guardada escribía `scoring_total` con el entorno sudo del job. Ahora esa línea se relee con el entorno del docente antes del write. Además, un usuario que no es superusuario podía plantar `result_id` al crear una participación oral, o al convertir una participación normal en caso oral. Esos dos caminos quedan rechazados. La tercera ejecución falló solo el assert del test nuevo: el alta sudo de un artículo normal sí enlaza la libreta y `isep_gradebook` pone la nota a 0. El test separa ese efecto del ataque. Cuarta ejecución en `artifacts/odoo-tests-4.log`: 0 failed, 0 error de 38 tests.

Revisión de código: primera pasada bloqueada, segunda aprobada. Evidencia en `artifacts/code-review.txt`.

Validación independiente: sintaxis y suite en verde (`artifacts/validation-odoo-tests.log`).

E2E TestSprite, dos primeras pasadas: fail de entorno. La primera dejó /web en blanco por assets 500. La segunda entró al backend y no abrió Casos orales: el menú raíz de eLearning pide officer y los escenarios no llevaban el id del slide. No se reabrió implementación.

Tercera pasada, la única autorizada después de preparar el entorno. Base nueva `test_irg_oral_case_e2e_8297`, volumen `odoo16irg_e2e_data` montado en `/var/lib/odoo` tanto en la instalación como en el servidor de 8069. `website_slides` e `irg_oral_case` instalados. Assets de login, backend y frontend en 200. Docente de prueba en `group_op_faculty` y `group_website_slides_officer`; el menú eLearning y Casos orales salen en `load_menus`. Fixtures: curso publicado, slide article 3 en modo clips con tres URL https, alumna portal inscrita, entrega 3 con nota IA 8.2 y tres clips. TestSprite recibió las URLs directas `/slides/slide/3` y `/web#id=3&cids=1&menu_id=346&action=473&model=irg.oral.case.job&view_type=form`. Nueve escenarios, nueve pasados. La alumna ve el consentimiento y, al aceptar la cámara, el aviso de que el navegador no puede usarla: el clip 1 no llega porque va después de getUserMedia. El docente guarda 7.5. En la base, `official_score` es 7.5, la línea del cuaderno tiene `scoring_total` 7.5 y `write_uid` es el docente. `verification.json` pasa a `passed`. Evidencia en `artifacts/e2e-testsprite.txt`.

Limpieza de la validación anterior: se paró el Odoo local y se ejecutó `dropdb` de `test_irg_oral_case_clips_8297`. Limpieza de esta pasada: se paró el contenedor `odoo16irg_e2e`, `dropdb` de `test_irg_oral_case_e2e_8297` y se borró el volumen `odoo16irg_e2e_data`. `psql` ya no lista bases `test_irg`. El puerto 8069 quedó cerrado y se terminó el proceso de TestSprite.
