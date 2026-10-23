# Changelog - 2026-10-23 - Caso oral por tramos

## Cambios realizados

* `irg_oral_case` pasa a 16.0.2.0.0.
* Un caso puede seguir siendo un solo webm o una lista ordenada de tramos, configurada en el slide. El HTML del artículo es un contenedor; el reproductor vive en un asset del frontend.
* La entrega puede guardar varios clips. El servidor comprueba alumna, número, orden, tamaño, tipo y duración. Con la nota final ya confirmada no se reenvía.
* El modo de un solo vídeo sigue enviando a n8n el mismo multipart de antes. El modo por tramos documenta la petición y la respuesta en `addons-extra/extrairg/irg_oral_case/doc/n8n_contract.md`.
* El docente edita la nota final como número de 0 a 10. El módulo escribe la línea del cuaderno de esa alumna y de esa participación, con el usuario docente, y deja rastro en el chatter. La sugerencia de la IA no se copia.
* La línea del cuaderno, el adjunto, quién confirmó y cuándo los escribe solo el sistema. La vista no ofrece un selector de líneas ni de adjuntos. El vídeo se ve en el reproductor de la entrega, o hay un aviso de que no se conserva.
* Conservar la grabación es un ajuste del slide. Sigue apagado por defecto. La política de retención queda pendiente.

## Pendiente de decisión

* Si Odoo debe conservar las grabaciones. El interruptor existe y nace apagado.
* El texto de consentimiento es provisional y no ha pasado la revisión legal.
* El flujo de n8n no se ha modificado. El contrato de tramos está en el módulo para cuando se adapte el flujo.

## Validación

* Suite del módulo en una base local desechable: 0 fallos, 38 tests de post-instalación, repetida por un validador distinto del codificador.
* Revisión de código independiente, aprobada tras cerrar dos bloqueantes de la nota y de `result_id`.
* Revisión de seguridad del plan: sí, antes de implementar.
* TestSprite contra el Odoo local, tras preparar una base desechable con eLearning, assets en 200 y URLs directas: 9 de 9. La alumna llega al consentimiento y, sin cámara, al aviso de que no se puede continuar. El docente guarda 7.5 y la línea del cuaderno queda en 7.5. El detalle está en `missions/irg-oral-case-clips`.
