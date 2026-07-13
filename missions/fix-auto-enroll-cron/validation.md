# Revalidación independiente — `fix-auto-enroll-cron`

Fecha: 2026-07-13

Resultado global: **PASSED**.

La validación se repitió íntegramente después del ajuste S1 aprobado. Se usó exclusivamente
`/Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/docker-compose.local.yml`, montando
`/Users/ivrogo/.codex/worktrees/Odoo16iRG/fix-auto-enroll-cron/addons-extra` en modo lectura.
Las bases `fix_auto_enroll_revalidation_20260713c` y
`fix_auto_enroll_revalidation_20260713d` son nuevas y aisladas. No hubo acceso de escritura
a `Base16`, beta o sistemas remotos, ni commit, push o despliegue.

## Evidencia automática fresca

- `irg_auto_enroll_cron_robust`: 27/27, 0 fallos, 0 errores, 5963 queries.
- `irg_online_subject_opening` + `irg_online_clone_access_fix`: 13/13, 0 fallos,
  0 errores, 2181 queries.
- Sintaxis Python: PASS en 17 archivos.
- XML: PASS con `xmllint`.
- Diff: PASS con `git diff --check`.
- Instalación y carga de registry Odoo en bases nuevas: PASS.

## T1.1 — persistencia `noupdate`

En `fix_auto_enroll_revalidation_20260713c`, el cron empezó en 1 hora. Se cambió localmente
a 2 horas, se ejecutó `-u isep_elearning_custom` y permaneció en 2 horas. Después se
restauró a 1 hora. PASS.

## T4.2 — reproducción literal del fallo previo

Se creó una admisión `done`, `manual`, con diez memberships activas y se movió al pasado una
sola línea. No hubo activaciones compensatorias en ese run:

```text
initial_active=10
pending triggers=1
processed=21 activated=0 archived=1 errors=0
```

“Run manually” archivó la membership objetivo. El ratio fue 1/10, por debajo del umbral.
Se conservaron los diez IDs y quedaron nueve memberships activas.

Al mover la fecha al futuro apareció de nuevo exactamente un trigger. “Run manually”
registró `activated=1, archived=0`, reactivó el mismo ID y no creó duplicados. Una tercera
ejecución registró `activated=0, archived=0` y conservó los mismos diez IDs activos. PASS.

## Guardarraíl >30% y rollback

En un caso separado se partió de las mismas diez memberships activas y se llevaron cuatro
líneas al pasado. El cron registró:

```text
processed=21 activated=0 archived=4 errors=0
initial_active=10 ratio=40.00%
```

Se lanzó el `ValidationError` esperado y el savepoint exterior restauró exactamente los diez
estados iniciales. PASS.

## Índice, preflight, uninstall y triggers

- Índice instalado con la clave y predicado requeridos.
- Cero grupos activos duplicados.
- Desinstalación real: módulo `uninstalled` e índice ausente.
- Preflight real: dos filas duplicadas provocaron exit 255; ambas quedaron intactas y el
  índice no se creó. El fixture se retiró después.
- Estado final del cron en la base principal de revalidación: activo, cada 1 hora y cero
  triggers residuales.

Todos los checks pasan.

## SQL reversible

El informe read-only se ejecutó correctamente. El backfill produjo `UPDATE 0`, `UPDATE 0` y
`ROLLBACK`; filas y checksum fueron idénticos antes y después:

```text
rows=32
checksum=71297b6448d98608f05b7f80f8cda298
```

Los scripts no están cargados por ningún manifest, XML o Python.

## Evidencia

- `artifacts/test-output.log`
- `artifacts/robust-suite-revalidation.log`
- `artifacts/regression-suite-revalidation.log`
- `artifacts/noupdate-upgrade-revalidation.log`
- `artifacts/manual-t42-revalidation.log`
- `artifacts/manual-guardrail-revalidation.log`
- `artifacts/uninstall-cycle-revalidation.log`
- `artifacts/preflight-install-revalidation.log`

El contrato `verification.json` queda en `passed`. La misión puede avanzar a la fase de
Documentación, manteniendo el gate de no commit/push/deploy sin autorización explícita nueva.
