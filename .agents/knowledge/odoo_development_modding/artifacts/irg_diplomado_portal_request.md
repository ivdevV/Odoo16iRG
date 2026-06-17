# Patron: Solicitudes portal de diplomas de diplomados

Fecha: 2026-06-16

Modulo: `irg_diplomado_portal_request`

## Decision reutilizable

Para separar diplomas de diplomados del flujo general de certificados/masteres, usar un modulo nuevo con rutas dedicadas `/campus/diplomados/...`.

El flujo portal debe descargar directamente el diploma. No debe dejar una solicitud pendiente para secretaria academica: si el alumno cumple `total_final > 7.0`, el POST crea o reutiliza `irg.diplomado.registry`, genera el adjunto PDF con `action_reprint()` si falta y responde con el binario.

## Motivos

- Evita colisiones con el intento anterior que usaba `irg.diplomado.request`.
- No modifica modulos existentes.
- No mezcla diplomados con `irg.certificate.request` ni con el portal de diplomas de masteres.
- Permite aplicar la regla academica `total_final > 7.0` tanto en UI como en backend.
- Evita un estado artificial de "En tramite" cuando el resultado esperado de negocio es descarga inmediata.

## Gotchas detectados

- `app.gradebook.subject.final_subject_note` es computed/stored y puede recalcularse a `0.0` si no hay resultados de examen. En tests enfocados conviene mockear `compute_final_subject_note()` o crear resultados reales.
- `HttpCase` necesita un puerto libre. Si el servicio `odoo_local` ya ocupa `8069`, ejecutar pruebas con `--http-port=8099`.
- La ruta `/campus/course/<id>` depende de contexto de perfil; para probar inyecciones QWeb de tiles puede ser mas estable validar la vista heredada y probar el flujo funcional por rutas dedicadas.
- En tests de descarga directa se puede mockear `irg.diplomado.registry.action_reprint()` para adjuntar un PDF determinista y evitar depender del render ReportLab completo.

## Comando validado

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_diplomado_portal_request --test-enable --test-tags /irg_diplomado_portal_request --stop-after-init --http-port=8099 --log-level=test
```
