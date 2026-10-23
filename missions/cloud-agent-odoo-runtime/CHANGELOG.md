# Changelog — cloud-agent-odoo-runtime

- Añade el entorno de Cloud Agents (`.cursor/environment.json`, Dockerfile, install y start) para poder ejecutar `docker-compose.local.yml` dentro de la VM.
- La plantilla vive en `.cursor/runtime/` porque `docker-compose.*.yml` y `etc/` están ignorados. El compose de la raíz se genera y no se versiona.
- Documenta que el entorno personal actual no lee el archivo y que un Build de `main` no lo incluye hasta que el cambio esté en `main`.
- Ejecuta los tests de `irg_oral_case` en una base desechable. Quedan 2 errores de 20 tests, sin corrección del módulo. TestSprite no se ejecuta.

El changelog por fecha del repositorio es `CHANGELOG_2026-10-23_cloud_agent_runtime.md`.
