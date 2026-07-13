# Fase 0 — Diagnóstico de solo lectura

Fecha: 2026-07-13

Entornos consultados:

- Local: contenedores `odoo16irg_local` / `pgodoo16irg_local`, base
  `test_irg_db` (dataset local útil para este flujo).
- Beta: `ssh odoobetairg`, contenedores `nat16_odoo_latest` /
  `nat16_pgodoo_latest`, base `Base16`.

Todas las consultas de base de datos fueron `SELECT`. No se ejecutó ninguna escritura,
actualización de módulo, trigger manual, reinicio o despliegue.

## T0.1 — Estado del cron

| Entorno | Active | Intervalo | Nextcall | Lastcall |
|---|---:|---|---|---|
| Local (`test_irg_db`) | true | 1 day | 2026-06-19 07:17:44 | 2026-06-18 08:38:02 |
| Beta (`Base16`) | true | 1 day | 2026-07-13 18:49:16 | 2026-07-12 18:49:25 |

H1 queda confirmada en ambos entornos: el registro real es diario.

## T0.2 — Logs

Local:

- `test_irg_db`: `Starting job Auto Enroll Students` y `Job ... done` el
  2026-06-18; no aparece error en ese run.
- La base local mínima `odoo16irg_local`, descartada como dataset de diagnóstico por no
  tener instalado `isep_subject_precedence`, sí muestra un fallo el 2026-06-24:
  `op.admission` no tenía `cron_auto_enroll_student`. No se atribuye este fallo al dataset
  válido `test_irg_db`.

Beta:

- No hubo coincidencias en los logs retenidos de `nat16_odoo_latest` para
  `Auto Enroll Students`, `cron_auto_enroll_student`, `Job .* failed`, límites CPU o
  límites de tiempo real.
- La ausencia de coincidencias no permite descartar H3; `lastcall` prueba que el cron sí
  registró ejecución el 2026-07-12.

## T0.3 — Modalidad

| Entorno | Auto | Manual |
|---|---:|---:|
| Local (`test_irg_db`) | 30 | 0 |
| Beta (`Base16`) | 666 | 522 |

H2 queda confirmada en beta. Las 522 admisiones manuales incluyen cursos afectados de las
dos familias señaladas por el plan. Ejemplos con admisiones manuales:

- Máster en Psicología Clínica y de la Salud: 114.
- Máster en Neuropsicología Clínica Basada en la Evidencia: 44.
- Diplomado en Evaluación e Intervención desde las Terapias de Tercera Generación: 89.
- Diplomado en Neuroeducación: Intervención y Desarrollo Cognitivo: 74.

El checkpoint de Fase 0 es obligatorio antes de decidir el domain definitivo de T2.1.

## T0.4 — Dimensionado y datos históricos

| Métrica | Local (`test_irg_db`) | Beta (`Base16`) |
|---|---:|---:|
| Admisiones done con lote | 30 | 1,188 |
| Media asignaturas por lote no vacío | 7.10 | 17.37 |
| Máximo asignaturas en un lote | 40 | 535 |
| Lotes con asignaturas | 10 | 117 |
| Memberships totales | 20 | 5,283 |
| Sin `admission_id` | 19 | 443 |
| Sin `op_subject_id` | 19 | 354 |
| Sin alguno de ambos | 19 | 443 |

H4 queda confirmada en ambos entornos. Por tanto, Fase 3 aplica.

El volumen beta respalda exactamente el trade-off del plan: cron horario como red de
seguridad y `_trigger()` ante cambios, no full-scan cada 15 minutos.

## Diagnóstico adicional de concurrencia autorizado

Consulta read-only en beta del 2026-07-13:

- Grupos duplicados activos por `partner_id + channel_id`: 0.
- Grupos duplicados activos por `partner_id + channel_id + batch_id`: 0.
- Grupos duplicados incluyendo activas y archivadas por alumno/canal/lote: 213
  (215 filas adicionales), que no se modificarán.
- Alumnos activos simultáneamente en un canal Homeclass y su clon Online: 92.

Resultado: el índice parcial se restringe a activas por alumno/canal/lote. No bloquea
Homeclass→Online porque los canales original y clonado son distintos, y tampoco bloquea
lotes distintos aunque compartieran canal.

## Estado de hipótesis

| Hipótesis | Local | Beta |
|---|---|---|
| H1 intervalo diario / `noupdate=0` | Confirmada | Confirmada |
| H2 modalidad manual excluida | No presente en el dataset | Confirmada |
| H3 excepción/rollback | No confirmada en dataset válido | Sin evidencia suficiente |
| H4 históricos sin referencias | Confirmada | Confirmada |
