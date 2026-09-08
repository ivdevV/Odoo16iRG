# Mission Plan: irg-diplomado-class-start-date

## Fuente

- Spec: `docs/superpowers/specs/2026-09-04-irg-diplomado-class-start-date-design.md`
- Plan TDD: `docs/superpowers/plans/2026-09-04-irg-diplomado-class-start-date.md`
- Rama prevista: `feat/irg-diplomado-class-start-date` (desde `Dev_iRG`)

## Knowledge

- `modding_rules_and_email_analysis.md` — módulo nuevo `irg_`, herencia, no editar existentes.
- `irg_diplomado_portal_request.md` — portal crea/reutiliza registro y solo regenera PDF si falta adjunto.
- `portal_diplomados_download.md` — ruta campus `/campus/certificates/download/diplomado/<id>` con el mismo patrón.
- `irg_diplomado_website_verify_qr.md` — `_get_diplomado_pdf_data()` y `action_reprint()` sin `super()`.
- `irg_diplomado_fixed_issue_date.md` — no tocar `issue_date`.
- `diplomado_report_layout.md` — el PDF emitido es ReportLab.
- `doc/flujo_automatricula_analisis.md` — `op.batch.date_start_class` ≠ `start_date`.

## Clasificación

- Misión: `full`
- Tier: `standard` (módulo nuevo, lógica acotada, mutación del PDF emitido)
- E2E: **obligatorio** (hereda controladores HTTP de portal)
- Security Advisor: **obligatorio** antes de implementar (sobrescribe el adjunto PDF ya emitido)

## Roles

- Plan / orquestación: esta sesión
- Implementación/TDD: esta sesión (módulo acoplado; no subagentes por tarea)
- Review: agente distinto tras GREEN
- Validación: agente distinto; `verification.json`
- Documentación: tras Review y Validación
- Commit / push / PR: solo con autorización explícita

## Criterios de aceptación

1. El texto «celebrado del …» usa `date_start_class` del lote (fallback `start_date` si está vacío).
2. Wizard y portal de alta copian esa fecha a `irg.diplomado.registry.start_date`.
3. Cada `action_reprint` y cada descarga de portal sincronizan la fecha desde el lote y regeneran el PDF.
4. Se reescribe `attachment_id.datas`; no se crea un segundo adjunto.
5. Fecha de fin y fecha de expedición (26 de septiembre) no cambian.
6. Diplomas de graduación fuera de alcance.
7. Tests de módulo GREEN en `docker-compose.local.yml`; E2E TestSprite obligatorio.

## Comando canónico

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_generacion_diplomados_class_start_date --test-enable \
  --test-tags=/irg_generacion_diplomados_class_start_date \
  --stop-after-init --http-port=8099 --log-level=test
```
