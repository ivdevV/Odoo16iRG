# Plan — runtime local de Cloud Agents

## Clasificación

- Misión: `full`
- Tier: `standard`
- Motivo: configuración de entorno y runtime de agentes. No hay lógica de producto ni más de cinco archivos de módulo, pero `PROJECT.md` trata el runtime Docker como zona sensible y el encargo fija el mínimo en `standard` con Security Advisor previo. No es `complex`: el cambio no toca autenticación de Odoo, migraciones, secretos existentes, Jenkins ni código de módulos.
- Security Advisor: obligatorio antes de cualquier archivo de runtime. La ronda 1 quedó `[NO]` en `artifacts/security-advisor.txt` y el plan ya incorpora ese cambio. Hace falta un `[YES]` nuevo en `artifacts/security-advisor-r2.txt` antes de implementar.
- E2E TestSprite: el diff previsto no toca vistas, assets, portal, website ni controladores. El check `e2e_testsprite` queda `skipped` por scope. El usuario pidió, además, una demostración aparte (`e2e_demo`) contra `irg_oral_case`, un solo intento, solo si los tests del módulo han pasado, el MCP está disponible y hay crédito. `projectPath` es únicamente `addons-extra/extrairg/irg_oral_case`. Si la demostración falla, se documenta y no se edita el módulo; no se relanza salvo fallo de infraestructura.

## Capacidad

Runtime de este agente (Grok 4.7). No hay selector de modelo real; no se inventa otro tier de modelo. Los roles de Security Advisor, Review y Validación son subagentes distintos del codificador.

## Entorno Cursor ya existente

Consulta `environment-info` del 2026-10-23:

- Entorno personal `e45fa8d1-ce18-11f1-89ee-7aa6f0729b11`, `source: Personal`, `recordedVia: RUNTIME_FORWARD_FILL`.
- `environmentJsonPath`: null. Es un entorno de panel, no lee `.cursor/environment.json`.
- Egress: sin restricción.
- La rama por defecto de GitHub es `main`. La rama de integración del equipo es `Dev_iRG`. Jenkins despliega beta al actualizar `Dev_iRG` y producción al actualizar `main`. Esta misión no fusiona ni hace push a ninguna de las dos.
- En esta VM no hay Docker. Sí hay `/dev/fuse`, `sudo` sin contraseña, Node en `/exec-daemon/node` y el namespace MCP TestSprite en estado `ready`. Ubuntu 24.04.

Un `.cursor/environment.json` comprometido no cambia este entorno. Hace falta que la ubicación del entorno apunte a ese archivo, o que el usuario guarde una propuesta de snapshot. Los Builds leen la rama por defecto del entorno (`main` en GitHub) salvo un ref explícito de prueba. Fusionar solo en `Dev_iRG` no mete el Dockerfile en un Build de `main`.

## Conocimiento consultado

- `AGENTS.md` (runtime local, capa E2E, gates, secretos).
- `PROJECT.md` (stack Odoo 16 / PostgreSQL 16 / Redis, comando canónico, zonas sensibles, base `Dev_iRG`).
- `SPECIFICATIONS.md` (no tocar core; changelog).
- `.gitignore`: `docker-compose*.yml`, `docker-compose.*.yml` y `etc/` están ignorados. Por eso `docker-compose.local.yml` no está en el repo y la misión de `irg_oral_case` no pudo ejecutar tests (`missions/irg-oral-case/execution.md`).
- `addons-extra/extrairg/irg_oral_case/__manifest__.py` y el cierre de dependencias: 16 módulos propios o de OpenEduCat presentes en el repo. Los que faltan (`survey`, `website_slides`, `account`, `hr`, `mail`, `web`, …) son del núcleo y vienen en la imagen oficial `odoo:16.0`. Ninguno declara `external_dependencies`.
- Documentación vigente de Cursor Cloud Agents: [setup](https://cursor.com/docs/cloud-agent/setup) (resolución de entorno, Builds, Running Docker con `fuse-overlayfs` e `iptables-legacy`) y [schema](https://cursor.com/schemas/environment.schema.json). El schema rechaza campos no declarados; no se añade `$schema`.
- `environment-info` y los esquemas de `trigger-environment-build` / `propose-environment-json`: en un entorno de panel la propuesta solo admite `install` y `start`; el snapshot va en el build, no en la propuesta.

## Alcance

Incluye:

- `.cursor/environment.json`, `.cursor/Dockerfile`, `.cursor/install.sh`, `.cursor/start.sh`.
- Plantilla de compose y `odoo.conf` locales, sin secretos, bajo `.cursor/runtime/`. El nombre no coincide con el patrón ignorado `docker-compose.*.yml`.
- `install.sh` materializa `docker-compose.local.yml` en la raíz antes de cualquier comando Compose, solo si no existe o si la primera línea es el centinela exacto `# cursor-cloud-runtime-generated: odoo16irg-local-v1`. No pisa un compose de desarrollador. Si el archivo existe sin ese centinela, no se toca y los comandos siguen usando `-f docker-compose.local.yml`: no hay caída a `docker-compose.yml`.
- Tests de contrato del runtime en `missions/cloud-agent-odoo-runtime/`.
- Documentación de cómo Cursor lee la configuración, qué hace falta para que aplique y el changelog por fecha.
- Una sección corta en `AGENTS.md` que apunte a esa documentación (fase de Documentación).
- Demostración en esta VM: Docker, PostgreSQL desechable, tests de `irg_oral_case`.
- Tras la validación local: snapshot, build borrador y propuesta para que el usuario pueda guardar el entorno de panel. Eso no sustituye el archivo del repo.

Fuera de alcance:

- Código de producción de cualquier módulo, incluido arreglar tests de `irg_oral_case` si fallan.
- `etc/`, `docker-compose.yml`, `Jenkinsfile`, `docker/`, credenciales existentes.
- Push a `Dev_iRG`, `main` o `dev_iRG`. Merge. Apuntar TestSprite a beta o producción.
- Cambiar egress, allowlists de MCP o secretos de Cursor. `TESTSPRITE_API_KEY` ya está en Cursor; no se escribe en ningún archivo.

## Diseño

### Base de la imagen

Dockerfile `FROM ubuntu:24.04`, usuario `ubuntu` ya existente (no se crea). Instala git, curl, ca-certificates, sudo, python3, Node 22 en `/usr/local` (el login shell no lee `~/.bashrc`) y Docker CE con el patrón oficial de Cursor: `fuse-overlayfs`, `daemon.json` con ese storage driver, `iptables-legacy` e `ip6tables-legacy`, grupo `docker` y sudo sin contraseña. No se copia el repositorio. No se fija la contraseña de ejemplo `ubuntu:ubuntu` del snippet de Cursor: esta VM ya entra con sudo sin contraseña y no queremos una credencial en el repo.

La versión de Docker del snippet (`5:28.5.2-1~ubuntu.24.04~noble`) se usa si el repositorio apt aún la publica. Si no, se registra en `execution.md` la versión disponible que sí instala y se fija esa. No se deja sin pin.

`environment.json`:

- `name`, `user: ubuntu`
- `build.dockerfile: Dockerfile` (relativo a `.cursor`; sin `context`, para que el contexto sea `.cursor` y no el árbol con `etc/` ignorado)
- `install` y `start` que invocan los scripts si existen, para que un Build de `main` anterior al merge no falle en seco
- `ports` 8069 y 8072

No se combinan `snapshot`, `image` y `build`. No se pone un snapshot personal en el archivo versionado.

### Runtime Odoo

Imagen pública `odoo:16.0` y `postgres:16`. No se usa el id de imagen ni la contraseña del `docker-compose.yml` de despliegue.

Servicios, alineados con los nombres que ya usan las misiones:

- `pgodoo_local`: PostgreSQL 16, usuario `odoo`, contraseña local `odoo` (el ejemplo público de la imagen oficial; solo red de compose; el puerto no se publica al host).
- `odoo_local`, contenedor `odoo16irg_local`: publica `127.0.0.1:8069` y `127.0.0.1:8072`. Monta `./addons-extra` en `/mnt/extra-addons` solo lectura. El conf montado es `.cursor/runtime/odoo.conf`, nunca `etc/`.
- `redisodoo_local`: presente porque `PROJECT.md` lo lista en el runtime local. Odoo no lo usa como sesión en este conf.

`odoo.conf` sin hosts de beta ni producción: `db_host = pgodoo_local`, `admin_passwd = local-disposable`, `list_db = False`, `workers = 0`, `addons_path` limitado a `extrairg`, `addons_uisep`, `community-16`, `enterprise-16` y los addons de la imagen. No se escanea el resto de `addons-extra`.

Selección de Compose, obligatoria en `install.sh`, `start.sh`, pruebas y documentación. Toda invocación es `docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml` y ninguna otra `-f`. No se define `COMPOSE_FILE`, no se carga `docker-compose.override.yml` y no se usa el nombre por defecto, que en esta máquina resolvería el compose de despliegue. `compose.env` solo existe para no interpolar el `.env` del directorio del proyecto; no contiene secretos. El YAML no usa `${...}`.

El bloque `environment` de Postgres lleva usuario, contraseña y base como literales. El servicio Odoo no declara `environment` ni `env_file`: el entrypoint de la imagen oficial reescribe `db_host` y la contraseña si ve esas variables, y un traspaso del entorno del host podría apuntar la base a un host que ya estuviera en la VM. La configuración de base sale solo de `.cursor/runtime/odoo.conf`.

Volúmenes sin `external` y con nombres propios de este runtime (`odoo16irg_local_pgdata`), no los del stack de despliegue. Bind mounts solo dos: `./addons-extra:/mnt/extra-addons:ro` y `./.cursor/runtime/odoo.conf:/etc/odoo/odoo.conf:ro`. Sin `network_mode: host`, sin `privileged` y sin socket de Docker. Puertos publicados solo `127.0.0.1:8069` y `127.0.0.1:8072`. Postgres y Redis no publican puerto.

`install.sh` (termina, idempotente): instala Docker si falta, materializa el compose con la guarda del centinela y, solo después, arranca el daemon el tiempo justo para `docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml pull`. Al salir para el daemon. `start.sh` (cada arranque, reentrante): arranca Docker, espera `docker info`, levanta solo `pgodoo_local` con el mismo `-f` y espera salud. No deja Odoo residente: los tests usan `docker compose run` con el mismo `-f` y así el puerto 8069 queda libre. El agente que necesite HTTP lo levanta él.

En `environment.json`, `install` y `start` son un `if` sobre la existencia del script: salen 0 si el script aún no está en la rama y propagan el código de salida si el script existe y falla. No es un `&&` a secas, que fallaría también cuando el archivo no está.

### Prueba del módulo

Base desechable con nombre único, no `test_irg_db`. Comando canónico con `-i` (instalación limpia) y `--test-tags=/irg_oral_case`. Los tests del módulo son `post_install`. Si fallan, se guarda la evidencia y no se corrige el módulo.

Al terminar se borra la base desechable y se para el contenedor efímero. Evidencia de la limpieza.

### TDD

El contrato del runtime sí admite un test antes de los archivos de configuración. RED antes de crear `.cursor/`. El test falla si la plantilla, el conf o los scripts:

- invocan Compose sin `-f docker-compose.local.yml`, con otra `-f`, con `COMPOSE_FILE`, o con `docker-compose.override.yml`;
- hacen el pull antes de materializar, o reemplazan un compose cuya primera línea no es el centinela `# cursor-cloud-runtime-generated: odoo16irg-local-v1`;
- nombran `odoobetairg.laramieuniversity.com` o `app.institutoraimongaja.com`;
- contienen `etc/`, `env_file`, `${`, `network_mode: host`, `privileged`, el socket de Docker, `external:` o un volumen con nombre del stack de despliegue;
- publican un puerto que no sea `127.0.0.1:8069` o `127.0.0.1:8072`;
- montan algo distinto de `./addons-extra` solo lectura y de `.cursor/runtime/odoo.conf`.

La prueba real del daemon y de Odoo no cabe en ese unittest; va a Validación y queda dicha en `execution.md`.

### Entorno de panel, además del archivo

Cuando la validación local pase: snapshot de esta VM, build borrador con ese snapshot y los scripts, verificación en un subagente fresco si la herramienta lo permite, y `propose-environment-json` con el `buildId`. La propuesta no guarda el entorno. El usuario tiene que pulsar Save. Un build con ref de esta rama se puede probar y puede no ser promocionable; se dice en la PR.

## Criterios de aceptación

1. `.cursor/environment.json` valida contra el schema vigente y no contiene secretos.
2. En esta VM, `docker info` funciona y `docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml` levanta Postgres local. Ningún comando usa el compose de despliegue.
3. Los tests de `irg_oral_case` se ejecutan de verdad. El resultado, sea pass o fail, queda en `artifacts/` con el comando y la salida. Un fail del módulo no se arregla y no se disfraza de pass.
4. `verification.json` no declara `passed` si hay algún `fail`. Los `skipped` explican la causa.
5. La documentación dice dónde lee Cursor la configuración, que este entorno personal hoy no la lee, y que un Build de la rama por defecto `main` no incluye el Dockerfile hasta que el archivo esté en `main` y el entorno apunte al archivo.
6. Limpieza de la base desechable registrada.
7. PR draft única contra `Dev_iRG`, desde `cursor/cloud-agent-odoo-runtime-9bea`. Sin merge y sin push a `Dev_iRG`, `main` ni `dev_iRG`.

## Roles

| Fase | Rol |
| --- | --- |
| Plan | Orquestador |
| Security Advisor | Subagente distinto, antes de implementar |
| Implementación / TDD | Codificador |
| Review de código | Subagente distinto del codificador |
| Validación | Subagente distinto; no edita el runtime |
| E2E | Solo si el plan sigue en vigor y los checks previos pasan |
| Documentación | Documentador |
| PR draft | Responsable de entrega, autorización ya dada para esta rama |

## Riesgos

- Docker dentro de la VM de Cursor puede fallar pese al patrón oficial. Si falla, se documenta el error real y no se declara el check como pass. No se cambia a instalar Odoo en el host mientras el patrón oficial no se haya intentado: `AGENTS.md` exige `docker-compose.local.yml`.
- La imagen `odoo:16.0` puede no instalar el cierre OpenEduCat (demo, permisos, Python). Eso es un fallo de la prueba del módulo, no un arreglo de esta PR.
- El pull de imágenes es grande. El install de un Build tiene 90 minutos. El pull va en `install`, el daemon vivo va en `start`.
- Guardar la propuesta actualiza el entorno personal del usuario; el archivo del repo no lo hace por sí solo. Hay que decirlo en la PR para que no se confunda con un merge.

## Publicación

- Rama: `cursor/cloud-agent-odoo-runtime-9bea` (el runtime de Cloud Agents exige el prefijo `cursor/` y el sufijo `-9bea`; `PROJECT.md` prefiere `feat/<misión>`. Se explica en la PR).
- PR draft contra `Dev_iRG`.
- Autorización de esta ejecución: push de esta rama y una PR draft. No autoriza merge ni push a las ramas de despliegue.
