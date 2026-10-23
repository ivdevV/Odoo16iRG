# Entorno de Cloud Agents para el runtime local de Odoo

Este documento dice cómo un agente de Cursor en la nube levanta el runtime que exige `AGENTS.md`: Docker Compose local, PostgreSQL desechable y, cuando toca, TestSprite contra `127.0.0.1:8069`. No describe el despliegue de beta ni el de producción.

## Dónde lee Cursor la configuración

Hay dos sitios, y no son lo mismo.

1. **Archivo del repositorio.** `.cursor/environment.json` (schema público: <https://cursor.com/docs/cloud-agent/setup>). Lo acompañan `.cursor/Dockerfile`, `.cursor/install.sh` y `.cursor/start.sh`. El Dockerfile instala Docker CE `5:28.5.2` con `fuse-overlayfs` e `iptables-legacy`, Node 22 en `/usr/local` y Python 3. La imagen base es `ubuntu:24.04` y el usuario es `ubuntu`. El contexto de build es `.cursor`: no se copia el repositorio.
2. **Entorno guardado en el panel.** Un entorno ya creado usa la configuración que tiene grabada. Solo lee el archivo del repo si su ubicación de `environment.json` apunta a ese archivo.

Orden en el que Cursor elige entorno, según la documentación vigente: primero el entorno personal guardado, después el de equipo, y al final `.cursor/environment.json` cuando un arranque crea un entorno nuevo para un único repositorio que todavía no tiene uno y el archivo comprometido es válido.

Este repositorio ya tiene un entorno personal. El 2026-10-23 `environment-info` lo mostró con `environmentJsonPath` vacío (`e45fa8d1-ce18-11f1-89ee-7aa6f0729b11`). Ese entorno no lee `.cursor/environment.json`. Fusionar el archivo no lo cambia. Para que lo lea hay que apuntar la ubicación del entorno al archivo, o crear un entorno nuevo que lo registre. Guardar una propuesta de snapshot en el panel actualiza el entorno personal por otra vía: la propuesta no sustituye al archivo versionado, y el archivo versionado no guarda el panel.

Los Builds usan la rama por defecto del entorno. En GitHub la rama por defecto de este repo es `main`. Un Build de `main` no incluye el Dockerfile ni los scripts hasta que estén en `main`. Fusionar solo en `Dev_iRG` deja el archivo en la rama de integración del equipo y permite que un agente arrancado sobre esa rama lo vea después del checkout, pero el Build que hornea la imagen sigue saliendo de `main` mientras el entorno construya esa rama. Hace falta el archivo en `main` para que esos Builds lo incorporen. Esta misión no fusiona en `main` ni en `Dev_iRG`. Jenkins despliega beta al actualizar `Dev_iRG` y producción al actualizar `main`.

`install` corre en el Build, tiene que terminar y no deja procesos vivos. `start` corre en cada arranque del agente, en segundo plano, y Cursor no espera a que acabe. Un snapshot no conserva procesos: el daemon de Docker va en `start`, no en `install`.

Las máquinas self-hosted no leen `.cursor/environment.json`.

## Qué hay que ejecutar

`docker-compose.local.yml` está en `.gitignore` (`docker-compose.*.yml`) porque en las máquinas de desarrollo puede convivir con el compose de despliegue. `install.sh` lo copia desde `.cursor/runtime/odoo-local-compose.yml` solo si no existe o si su primera línea es el centinela `# cursor-cloud-runtime-generated: odoo16irg-local-v1`. Un compose de un desarrollador, sin ese centinela, no se toca.

Toda invocación lleva el archivo local y un env file propio, para no leer `docker-compose.yml` ni un `.env` del proyecto:

```bash
docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml <comando>
```

Sin `-f`, Compose abre el compose de despliegue si ese archivo está en disco. No se define `COMPOSE_FILE` y no se mezcla `docker-compose.override.yml`.

`bash .cursor/start.sh` arranca Docker y deja `pgodoo16irg_local` en healthy. No deja Odoo residente, para que el puerto 8069 quede libre. Quien necesite HTTP hace `up -d odoo_local` con el mismo `-f`. Como Cursor no espera a `start`, antes de un test hay que comprobar el health o volver a lanzar `start.sh` (se puede repetir).

Tests de un módulo, en una base nueva, no en `test_irg_db` ni en `Base16`:

```bash
docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d <bd_desechable> -i <modulo> \
  --test-enable --test-tags=/<modulo> --stop-after-init \
  --workers=0 --http-port=8099 --log-level=test
```

Al terminar: `docker exec pgodoo16irg_local dropdb -U odoo --if-exists <bd_desechable>`.

## Qué contiene el runtime

- Imágenes públicas `odoo:16.0`, `postgres:16` y `redis:7`. No es la imagen privada del compose de despliegue.
- Postgres solo en la red de Compose. Usuario y contraseña `odoo` / `odoo`, el ejemplo público de la imagen oficial. No se publica el puerto. Redis tampoco.
- Odoo publicado solo en `127.0.0.1:8069` y `127.0.0.1:8072`. El conf es `.cursor/runtime/odoo.conf` (`db_host = pgodoo_local`, `admin_passwd = local-disposable`, `list_db = False`). No se monta `etc/`.
- Addons en solo lectura, con `addons_path` limitado a `extrairg`, `addons_uisep`, `community-16`, `enterprise-16` y los addons de la imagen.
- El servicio Odoo no recibe variables de entorno del host. El entrypoint de `odoo:16.0` respeta `db_host` si ya está en el conf.
- Node y `npx` quedan en `/usr/local/bin` dentro de la imagen, para el MCP stdio de TestSprite (`npx @testsprite/testsprite-mcp@latest`). La API key vive en los secretos de Cursor. No va en el repo.

TestSprite, cuando el scope lo dispare: `projectPath` solo el directorio del módulo, puerto local 8069, base desechable, usuario de esa base. Nunca beta (`odoobetairg.laramieuniversity.com`) ni producción (`app.institutoraimongaja.com`).

## Límites conocidos

- El patrón de Docker dentro de la VM es el de la documentación de Cursor (driver `fuse-overlayfs`, iptables legacy). En esta VM, el 2026-10-23, `docker info` respondió con Engine 28.5.2 y Postgres quedó healthy. No está probado en todas las regiones ni en self-hosted.
- `install` puede tardar: descarga `odoo:16.0`. El presupuesto de un Build es de unos 90 minutos. Si `install` falla, el Build anterior sigue vigente.
- La imagen oficial no es `odoo16irg:16.0-local`. Módulos que necesiten librerías Python ausentes de `odoo:16.0` fallarán al instalarse. Eso se documenta; no se parchea el módulo en la misma misión salvo que la misión sea esa.
- El 2026-10-23 los tests de `irg_oral_case` se ejecutaron de verdad sobre `test_irg_oral_case_9bea` y, en la validación independiente, sobre `test_irg_oral_case_validator`. Las dos veces: `0 failed, 2 error(s) of 20 tests`. Los errores están en el módulo (`TypeError` en `assertRaises` con una tupla, y `AccessError` al leer `slide.slide` desde el wizard). No se han corregido aquí. Por eso no se gastó el crédito de TestSprite. `verification.json` queda en `failed`.
- Un agente que arranque antes de que el archivo esté en la rama que el Build usa seguirá sin Docker hasta que el entorno personal se actualice con un snapshot o hasta que el Build nuevo esté activo.
