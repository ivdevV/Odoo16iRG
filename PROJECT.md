# PROJECT.md — Odoo16iRG

Capa de **hechos** del proyecto: stack, comandos canónicos, convenciones y zonas
sensibles. La política de **proceso** es `AGENTS.md` y prevalece sobre este
archivo en todo lo relativo a fases, gates, artefactos y autorizaciones. Si algo
aquí contradice a `AGENTS.md`, manda `AGENTS.md`.

Existe para que los agentes con un paso "lee `PROJECT.md`" (planner, reviewer,
validator, e2e-tester) no arranquen a ciegas.

## Stack

| Pieza | Versión / detalle |
| --- | --- |
| ERP | Odoo 16.0 (Community + Enterprise) |
| Lenguaje | Python 3, XML/QWeb, JS (assets Odoo) |
| BD | PostgreSQL 16 |
| Cache | Redis |
| Runtime | Docker Compose |
| Base académica | OpenEduCat |

## Layout de addons

`addons-extra/` agrupa 18 directorios de addons. Los relevantes:

- `extrairg/` — **167 módulos propios del Instituto Raimon Gaja**, prefijo `irg_`.
  Es donde vive casi todo el trabajo de misión.
- `addons_irg/`, `addons_uisep/` — addons iRG/UISEP adicionales.
- `community-16/`, `enterprise-16/`, `ent_addons/` — Odoo upstream. **No tocar.**
- `localizacion_espanola/`, `addons-mx/`, `addons-co/` — localizaciones ES/MX/CO.

El repo contiene 6375 `__manifest__.py` en total. Cualquier operación que asuma
que puede resumir o escanear "el proyecto entero" es inviable: acota siempre al
módulo de la misión.

## Runtime local

Todas las validaciones dependientes de runtime usan `docker-compose.local.yml`
(`AGENTS.md`, sección "Runtime local").

- Servicio Odoo: `odoo_local` / contenedor `odoo16irg_local`
- Puertos: `8069` (HTTP), `8072` (longpolling)
- Addons montados en `/mnt/extra-addons` (solo lectura)
- Config: `etc/odoo/odoo.local.conf` → `/etc/odoo/odoo.conf`
- BD de pruebas habitual: `test_irg_db`, o una BD desechable por misión
- En worktree se aplica un overlay `docker-compose.worktree.yml` que monta el
  checkout aislado

## Comandos canónicos

Sintaxis Python:

```bash
python3 -m py_compile addons-extra/extrairg/<modulo>/**/*.py
```

Sintaxis XML:

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('addons-extra/extrairg/<modulo>/views/<archivo>.xml')"
```

Tests de módulo (patrón real usado en las misiones; el overlay de worktree solo
aplica si trabajas en uno):

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u <modulo> --test-enable --test-tags=/<modulo> --stop-after-init --http-port=8099 --log-level=test
```

Instalación limpia sobre BD desechable (sustituye `-u` por `-i`):

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d <bd_desechable> -i <modulo> --test-enable --test-tags=/<modulo> --stop-after-init --http-port=8099 --log-level=test
```

**No hay linter ni formateador canónico** en este proyecto. Ningún
`verification.json` del histórico registra un comando de lint real. No inventes
uno ni declares `lint: pass` sin comando; si el plan no define lint, el check va
`skipped` con justificación.

## Cobertura E2E

`odoo --test-enable` no ejerce la capa web renderizada. La cobertura extremo a
extremo que exige `AGENTS.md:84` la aporta el gate `e2e_testsprite`, descrito en
la sección "Capa E2E" de `AGENTS.md`. Rol: `.claude/agents/e2e-tester.md`.

## Convenciones

- Módulos propios con prefijo `irg_`; nombre del directorio = nombre técnico.
- Los tests viven en `<modulo>/tests/` y requieren `tests/__init__.py` — sin él,
  Odoo no los descubre y reporta 0 tests sin error (ya pasó en
  `irg_online_subject_opening`).
- Los mensajes de commit siguen Conventional Commits, en español, con el módulo o
  área como scope: `fix(irg_stripe_payments): ...`.
- Conocimiento reutilizable en `.agents/knowledge/odoo_development_modding/artifacts/`.

## Git

- **Nunca se trabaja ni se ramifica desde `main`.** La rama base es `Dev_iRG`.
- Feature branches: `feat/<misión>` o `fix/<misión>` desde `Dev_iRG` actualizada.
- Remoto vía alias SSH `github-work`; `origin` = `git@github-work:ivdevV/Odoo16iRG.git`.
- `gh` requiere prefijo `direnv exec .`; sin él usa otra cuenta y falla.
- Commit, push y PR son autorizaciones **separadas y de un solo uso**
  (`AGENTS.md`, sección "Commit, push y PR"). Push a `Dev_iRG` exige autorización
  explícita nueva en ese momento. El agente nunca mergea.

## Zonas sensibles

Tocar cualquiera de estas activa al Security Advisor y exige tier `standard` como
mínimo:

- `etc/` — configuración Odoo con credenciales.
- `docker-compose*.yml`, `docker/` — runtime y despliegue.
- Módulos de pagos (`irg_stripe_payments`) e integraciones con terceros
  (Moodle, Chatwoot, Stripe, webhooks de admisión).
- Cualquier migración de datos o borrado histórico.
- Servidores **beta y producción**: `odoobetairg.laramieuniversity.com` y
  `app.institutoraimongaja.com`. Las misiones no escriben en ellos. El servidor
  beta corre en el contenedor `nat16_pgodoo_latest` sobre la BD `Base16`; no se
  toca su BD directamente.
