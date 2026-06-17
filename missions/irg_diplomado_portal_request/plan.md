# Mision: irg_diplomado_portal_request

## Alcance

Crear un modulo nuevo para gestionar solicitudes de diplomas de diplomados desde el portal del alumno, separado del flujo de certificados/diplomas de masteres y sin modificar modulos existentes.

## Knowledge base consultada

- `.agents/knowledge/odoo_development_modding/artifacts/portal_diplomados_download.md`: patrones de extension limpia del portal, descarga segura y filtrado academico.
- `.agents/knowledge/odoo_development_modding/artifacts/diplomado_report_layout.md`: uso de `irg.diplomado.registry` como registro emitido y adjunto PDF de diplomado.
- `.agents/workflows/odoo16_codebase_knowledge.md`: convencion de desarrollo en `addons-extra/extrairg/` y validacion Odoo local.

## Clasificacion de complejidad

Tier: `standard`.

Justificacion: modulo nuevo con modelo, controlador portal, vistas QWeb, seguridad y tests. Toca 2-5 areas funcionales con logica acotada. No toca autenticacion, concurrencia, migraciones, secretos/configuracion de despliegue ni borrado historico.

## Modelo por fase

- Plan: orquestador con modelo de razonamiento alto.
- Implementacion: tier `standard`, codigo Odoo 16 por herencia y modulo nuevo.
- Validacion: tier `standard`, pruebas Odoo con `docker-compose.local.yml`.
- Documentacion: tier ligero, documentacion operativa y knowledge reutilizable.

## Descomposicion

1. Crear modulo `irg_diplomado_portal_request` en `addons-extra/extrairg/`.
2. Crear modelo `irg.diplomado.portal.request` para evitar colisiones con el intento anterior `irg.diplomado.request`.
3. Extender `op.course` con helper local `irg_is_diplomado()` para detectar diplomados sin depender del modulo previo.
4. Crear controlador portal dedicado `/campus/diplomados/<course_id>` y endpoints de solicitud/descarga.
5. Inyectar tile especifico de diploma de diplomado en herramientas del curso y ocultar el tile generico en cursos diplomado.
6. Integrar solicitudes con `irg.diplomado.registry` al emitirse un diploma.
7. Crear vistas backend, secuencia y reglas de acceso.
8. Crear tests HttpCase para elegibilidad, tile, solicitud, descarga y vinculacion.
9. Validar con Odoo local mediante `docker-compose.local.yml` y emitir `verification.json`.
10. Documentar modulo y persistir knowledge reutilizable.

## Reglas de negocio

- Solo cursos tipo diplomado.
- Solo alumnos asociados al partner del usuario portal.
- Solo libretas `app.gradebook.student` en `state = done`.
- Nota final estrictamente mayor que 7.0.
- No duplicar solicitudes activas ni diplomas emitidos para el mismo alumno y curso.
- La descarga del PDF requiere propiedad del alumno y nota final mayor que 7.0.

## Validacion prevista

Comando objetivo:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_diplomado_portal_request --test-enable --test-tags /irg_diplomado_portal_request --stop-after-init --log-level=test
```
