# Ejecución — widget de caso oral por clips

## Clasificación

Misión `full`, tier `complex`. Rama `cursor/oral-case-widget-729d` desde `Dev_iRG` (`d7756f3b8`, PR #54 ya fusionada).

## Decisiones

- 2026-10-23: el plan se escribe antes de cualquier cambio funcional. Ver `plan.md`.
- El runtime local (`docker-compose.local.yml`) no está en `Dev_iRG` (gitignore) y en esta VM no hay Docker al empezar. Se intentará materializar el runtime de `origin/cursor/cloud-agent-odoo-runtime-9bea` sin incluirlo en el diff.
- La skill que prohíbe editar módulos cede: el encargo nombra `irg_oral_case`.

## Seguridad

Revisión previa (agente distinto del codificador), sin cambios de código. Veredicto:

`[YES] Reason: El plan conserva nota oficial y campos de sistema solo en servidor, copia prompt a student_text vacío sin borrar datos, valida y sirve el MP4 autenticado con nosniff sin ejecutarlo, no envía la consigna de IA al navegador cuando hay student_text, y el cron root no escribe official_score ni registra la clave.`

Se puede implementar.

## Comandos

- RED de la lógica del widget, antes de crear `oral_case_logic.js`: `node --test addons-extra/extrairg/irg_oral_case/tests/oral_case_logic.test.js` → fallo, el archivo no existía.
- Tras la lógica y el reproductor: el mismo comando → 9 pruebas, 0 fallos.
- Suite Odoo, en curso, base desechable `test_irg_oral_case_widget_729d`, runtime local materializado sin commitearlo:

```bash
sudo docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_oral_case_widget_729d -i irg_oral_case \
  --test-enable --test-tags=/irg_oral_case --stop-after-init \
  --workers=0 --http-port=8099 --log-level=test
```

El Python de Odoo no se ejecutó en rojo antes del cambio: instalar el módulo y sus dependencias es una sola pasada larga. El rojo que sí corrió es el de Node. La causa queda aquí, antes de dar la suite por verde.

- Primera suite Odoo (`-i`, base `test_irg_oral_case_widget_729d`): 3 fallos de 45. `test_clips_are_sent_with_the_server_prompt` y `test_slide_flag_stores_the_clip_and_global_flag_still_does` enviaban bytes sin firma EBML y el sniffer nuevo devolvía `invalid_video_type`. `test_clip_duration_above_the_segment_is_rejected` leía el primer clip (basura) antes de mirar la duración del segundo. Corrección: validar orden y duración de todos los tramos antes de leer los ficheros, y firmar los payloads del camino feliz con EBML. Node se mantiene en 9/9.
- Segunda suite (`-u` sobre la misma base): `irg_oral_case: 59 tests`, `0 failed, 0 error(s) of 45 tests`, `EXIT:0`. Evidencia: `artifacts/odoo-tests.txt` y `artifacts/node-tests.txt`.
- El observador del padre no enganchaba un `iframe` añadido como nodo propio (tiene `querySelectorAll` y no es el documento). `scan` ahora llama a `watchFrame` cuando el nodo es un iframe. El medidor de audio no marca silencio hasta el primer frame y reanuda un `AudioContext` suspendido, para no bloquear «Usar esta respuesta» antes de medir.
- Review independiente (agente distinto): primer veredicto BLOCK. `clearInterval`/`clearTimeout` del padre no paran los temporizadores creados en el iframe `srcdoc`. Corregido: todas las cancelaciones usan `this.win`. También se rearma el plazo de «Responder ya» al empezar la reproducción, se ofrece repetir si la toma está en silencio y `allow_retry` es falso, y `www.vimeo.com` más `vimeo.com/ID/hash` se traducen al player. Segunda review: APPROVE.
- Validación independiente, base nueva `test_irg_oral_case_val_729d`: node 9/9, suite Odoo 0 fallos, py_compile 16 ficheros, el diff de producto queda en el módulo. `verification.json` lo registra.
- E2E: Odoo local en 8069, alumna desechable, slide HTTP 200 y el bundle contiene el reproductor. `testsprite_bootstrap` devolvió MCP -32001 dos veces. No hay tercer intento. La causa es el timeout del MCP, no un fallo de producto, así que no se reabre Implementación. Se escala en la PR. `status` de `verification.json` queda `failed` porque la capa E2E obligatoria no se ejecutó.
