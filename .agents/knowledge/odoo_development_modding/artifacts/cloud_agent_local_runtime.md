# Runtime local de Odoo en Cloud Agents

## Decisión

Los agentes en la nube ejecutan el runtime de `AGENTS.md` con Docker dentro de la VM, no con Odoo instalado en el host. La receta es la de Cursor para Docker anidado: Docker CE pinneado, `fuse-overlayfs` e `iptables-legacy`, daemon en `start`, pull de imágenes en `install`.

## Motivo

`docker-compose.local.yml` y `etc/` están en `.gitignore`. En una VM nueva no existen, y un `docker compose` sin `-f` abre el compose de despliegue si alguien lo tiene en disco. La plantilla versionada está en `.cursor/runtime/`. `install.sh` copia a `docker-compose.local.yml` solo con el centinela `# cursor-cloud-runtime-generated: odoo16irg-local-v1`. El comando siempre lleva `--env-file .cursor/runtime/compose.env -f docker-compose.local.yml`.

La imagen es la oficial `odoo:16.0` más `postgres:16`. El id de imagen y la contraseña del compose de despliegue no se reutilizan. Postgres no publica puerto. Odoo solo escucha en loopback del host. El conf no sale de `etc/`.

## Gotcha

Un `.cursor/environment.json` comprometido no cambia un entorno de panel cuya ubicación de archivo está vacía. Los Builds leen la rama por defecto del entorno. En este repo esa rama de GitHub es `main`, no `Dev_iRG`. El detalle operativo está en `doc/cloud-agent-environment.md`.
