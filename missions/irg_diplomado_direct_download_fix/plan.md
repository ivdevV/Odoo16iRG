# Mision: irg_diplomado_direct_download_fix

## Alcance

Corregir el flujo del modulo `irg_diplomado_portal_request` para que el boton del portal no deje una solicitud pendiente para secretaria academica. Al pulsar, si el alumno cumple los requisitos, debe generar/recuperar el diploma de diplomado y descargarlo directamente.

## Clasificacion de complejidad

Tier: `standard`.

Justificacion: cambio de comportamiento en controlador portal, plantilla QWeb, tests y documentacion. Logica acotada a un modulo ya creado, sin autenticacion, secretos, migraciones ni borrado historico.

## Knowledge base consultada

- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_portal_request.md`
- `.agents/knowledge/odoo_development_modding/artifacts/diplomado_report_layout.md`

## Plan

1. Cambiar `POST /campus/diplomados/<course_id>/request` para crear `irg.diplomado.registry` si no existe y descargar el PDF.
2. Mantener seguridad: curso diplomado, alumno propietario, libreta `done`, `total_final > 7.0`.
3. Eliminar del portal los textos de `Solicitud enviada`, `En tramite` y `Secretaria academica esta tramitando tu diploma`.
4. Actualizar tests para validar descarga directa tras pulsar el boton.
5. Validar con `docker-compose.local.yml` y actualizar `verification.json`.
