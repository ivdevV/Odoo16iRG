# Changelog - 2026-10-23 - Reproductor del caso oral por tramos

## Cambios realizados

* `irg_oral_case` pasa a 16.0.2.1.0.
* El reproductor arranca en la vista normal del slide, dentro del iframe `srcdoc` de `isep_content_interactive`, y sigue arrancando cuando el fullscreen pega el HTML en la página. No se modifica ningún otro módulo.
* El clip de la paciente se muestra a 16:9, con botón «Reproducir». Si Vimeo falla o no llega el final, aparece «Responder ya». La duración del clip solo se enseña si el player la reporta. El límite de la respuesta se etiqueta como tiempo máximo.
* Tras grabar solo quedan «Usar esta respuesta…» y «Repetir respuesta». Repetir vuelve a la consigna. Hay indicador textual de grabación. Los temporizadores se cancelan en la misma ventana donde se crearon.
* El servidor acepta WebM y MP4, comprueba la firma y el tamaño, y pone él el nombre del fichero. El contrato con n8n no añade campos; queda descrito en `addons-extra/extrairg/irg_oral_case/doc/n8n_contract.md`.
* Cada tramo separa el texto de la alumna (`student_text`) de la consigna de la IA (`prompt`). La migración copia el prompt al texto de la alumna solo si ese campo está vacío.
* El estado de la entrega sigue el estado remoto (`accepted`, `done` o `error`). Un cron consulta las entregas aceptadas. La nota oficial sigue siendo solo del profesorado.

## Pendiente de decisión

* El texto de consentimiento sigue siendo provisional.
* El guion clínico de Marta no se ha metido en el módulo.
* Conservar la grabación sigue apagado por defecto.
* El flujo de n8n no se ha editado. Tiene que aceptar el MP4 que ahora puede llegar en `video` o `clip_N`.

## Validación

* Lógica del reproductor con `node --test`: 9 pruebas, 0 fallos, repetida por el validador.
* Suite del módulo en una base local desechable: 0 fallos. El validador la repitió en `test_irg_oral_case_val_729d` (59 tests, 0 failed de 45 post-tests).
* Revisión de código independiente: aprobada tras cerrar el bloqueo de los temporizadores del iframe.
* TestSprite no llegó a ejecutar escenarios: `testsprite_bootstrap` agotó el tiempo dos veces (MCP -32001) con Odoo local en el puerto 8069. No se reintentó una tercera vez. La capa E2E no está validada.
