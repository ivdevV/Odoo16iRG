# Review de código — runtime local de Cloud Agents

Revisor distinto del codificador. Alcance limitado a `.cursor/environment.json`, `.cursor/Dockerfile`, `.cursor/install.sh`, `.cursor/start.sh`, `.cursor/materialize-compose.sh`, `.cursor/install-docker-packages.sh`, `.cursor/runtime/odoo-local-compose.yml`, `.cursor/runtime/odoo.conf`, `.cursor/runtime/compose.env` y `missions/cloud-agent-odoo-runtime/tests/test_runtime_contract.py`. No hay cambios de esta review sobre código de producción, `.cursor/`, módulos Odoo, `plan.md`, `execution.md` ni `verification.json`.

El unittest del contrato se ejecutó como comprobación del revisor (`python3 -m unittest missions.cloud-agent-odoo-runtime.tests.test_runtime_contract`): 8 tests, todos ok. Ese resultado no es el gate de validación.

## Contrato de Compose

`install.sh` y `start.sh` tienen una sola invocación cada uno:

- `sudo docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml pull`
- `sudo docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml up -d pgodoo_local`

Cada línea lleva `--env-file .cursor/runtime/compose.env`, una sola `-f` y el archivo `docker-compose.local.yml`. Los diez archivos revisados no contienen `COMPOSE_FILE`, `COMPOSE_ENV_FILES`, `docker-compose.override.yml` ni el nombre de archivo `docker-compose.yml`. `compose.env` solo tiene comentarios: no define variables ni secretos.

`install.sh` llama a `materialize-compose.sh` antes de arrancar el daemon y antes del `pull`. El centinela de la plantilla es la primera línea exacta `# cursor-cloud-runtime-generated: odoo16irg-local-v1`. Si `docker-compose.local.yml` ya existe y esa primera línea es distinta, el script sale 0 y no copia. Si no existe, o si la primera línea es el centinela, copia la plantilla.

## Compose, conf y red

YAML parseado de `odoo-local-compose.yml`:

- `pgodoo_local` y `redisodoo_local` no tienen `ports`. Postgres declara `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD` como literales (`postgres` / `odoo` / `odoo`) y el volumen nominado `odoo16irg_local_pgdata`, sin `external`.
- `odoo_local` publica solo `127.0.0.1:8069:8069` y `127.0.0.1:8072:8072`. No tiene clave `environment` ni `env_file`.
- Bind mounts: `./addons-extra:/mnt/extra-addons:ro` y `./.cursor/runtime/odoo.conf:/etc/odoo/odoo.conf:ro`. El volumen de Postgres es nominado, no bind. No hay `./etc`, `${`, `network_mode`, `privileged` ni socket de Docker.
- El alias de red `db` está en `pgodoo_local`. `odoo.conf` fija `db_host = pgodoo_local`, `admin_passwd = local-disposable` y `list_db = False`, sin `${` y sin hosts remotos.

Los textos revisados no nombran `odoobetairg.laramieuniversity.com` ni `app.institutoraimongaja.com`, ni los volúmenes de despliegue `odoo_latest`, `pgodoo_latest`, `dbfilestore` y `nat16_pgodoo_latest`.

## Imagen y environment.json

`environment.json` tiene `name`, `user`, `build.dockerfile`, `install`, `start` y `ports`. `build` solo declara `dockerfile`. No hay `$schema`, `snapshot`, `context` ni `image`. Los puertos son enteros 8069 y 8072. El esquema público vigente admite esos campos.

`install` y `start` son un `if [ -f ... ]` sin `|| true`. Si el script existe, la rama ejecutada es `bash` y el estado del `if` es el del script (un script de prueba con salida 7 se propaga). Si `install.sh` no existe, el `else` es `echo` y la salida es 0. Si `start.sh` no existe, el `else` es `sudo service docker start`: el archivo ausente no se evalúa como fallo de un `&&`, y un script presente que falla sigue propagando su código.

El Dockerfile parte de `ubuntu:24.04`, deja `USER ubuntu` y `WORKDIR /home/ubuntu`, y copia únicamente `install-docker-packages.sh`. No copia el repositorio. El script de paquetes fija `docker-ce` y `docker-ce-cli` en `5:28.5.2-1~ubuntu.24.04~noble`, instala `fuse-overlayfs`, escribe `daemon.json` con ese storage driver y selecciona `iptables-legacy` e `ip6tables-legacy`. No asigna la contraseña `ubuntu:ubuntu`. `bash -n` pasa en los cuatro scripts.

## Test de contrato

El test cubre el centinela con ejecución real de `materialize-compose.sh`: crea el archivo, lo deja igual en una segunda pasada, conserva un compose cuya primera línea no es el centinela y reemplaza uno que sí lo es. Cubre los rechazos de otra `-f`, de la ausencia de `--env-file .cursor/runtime/compose.env -f docker-compose.local.yml`, de `COMPOSE_FILE`, de `docker-compose.override.yml`, de `docker-compose.yml`, del `pull` anterior a materializar, de los hosts remotos, de los nombres de volumen de despliegue, de `env_file`, de `${` en plantilla, conf y scripts, de `network_mode`, de `privileged`, del socket, de `external:`, de `0.0.0.0`, de `./etc`, de un bloque `environment` en `odoo_local` y de puertos publicados distintos de las dos líneas de loopback. También fija la forma de `environment.json`.

APPROVED
