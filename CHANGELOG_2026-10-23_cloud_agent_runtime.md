# Changelog - 2026-10-23 - Runtime local para Cloud Agents

## Cambios realizados

* Nuevo entorno de Cursor en `.cursor/environment.json`, con Dockerfile (Docker CE 28.5.2, fuse-overlayfs, iptables legacy, Node 22, Python 3) e `install` / `start`.
* Plantilla de Compose y `odoo.conf` locales, sin secretos y sin montar `etc/`. `install.sh` materializa `docker-compose.local.yml` (sigue ignorado por git) solo si no existe o si lleva el centinela de este runtime.
* Postgres 16, Redis 7 y Odoo 16 oficiales. Odoo solo en `127.0.0.1:8069` y `127.0.0.1:8072`. Postgres sin puerto en el host.
* Test de contrato del runtime y documentación en `doc/cloud-agent-environment.md`.
* Nota corta en `AGENTS.md` para que el agente use siempre `-f docker-compose.local.yml`.

## Validación

* Contrato, sintaxis shell, `docker info` y Postgres healthy: pass, repetidos por un validador distinto.
* Tests de `irg_oral_case` ejecutados en base desechable: `0 failed, 2 error(s) of 20 tests`. No se ha tocado el módulo. El `verification.json` de la misión queda `failed` por esos dos errores.
* TestSprite no se ha ejecutado: el diff no toca superficie web y los tests del módulo no están en verde.

## Qué hace falta para que Cursor lo use

* Este entorno personal no lee el archivo (`environmentJsonPath` vacío). Hay que apuntar la ubicación del entorno a `.cursor/environment.json`, o guardar una propuesta de snapshot en el panel.
* La rama por defecto de GitHub es `main`. Un Build de `main` no ve el Dockerfile hasta que el archivo esté en `main`. Fusionar solo en `Dev_iRG` no basta para ese Build.
