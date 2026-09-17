# Mission Plan: irg-enrollment-modification

## Fuente

- Spec: `docs/superpowers/specs/2026-09-03-irg-enrollment-modification-design.md`
- Plan detallado TDD: `docs/superpowers/plans/2026-09-03-irg-enrollment-modification.md`
- Rama: `feat/irg-enrollment-modification` (desde `Dev_iRG`)

## Knowledge

- `modding_rules_and_email_analysis.md` — módulo nuevo `irg_`, herencia, no editar existentes.
- `irg_student_campus_block.md` — botón en `op.student`, `has_group()` en servidor, chatter sin `sudo()`.
- `irg_diploma_graduacion_student.md` — wizard desde estudiante, `ir.attachment`.
- `irg_physical_certificates_docx_layout.md` — `python-docx` + LibreOffice.

## Clasificación

- Misión: `full`
- Tier: `standard` (5–15 archivos, un módulo, seguridad de grupos y write de `payment_mode_id`)
- E2E: **obligatorio** (vistas estudiante + wizard)
- Security Advisor: obligatorio antes de implementar

## Roles

- Plan / orquestación: esta sesión
- Implementación/TDD: esta sesión (módulo acoplado; no subagentes por tarea)
- Review: agente distinto tras GREEN
- Validación: agente distinto; `verification.json`
- Push a `Dev_iRG`: solo con autorización nueva tras el código

## Criterios de aceptación

1. Botón oscuro «Modificación de matrícula» en la ficha `op.student` para el grupo académico.
2. Wizard con matrícula origen siempre y cinco casillas que despliegan origen/destino.
3. Crear solicitud adjunta `solicitud.docx` y no escribe curso ni pago.
4. Visto académico escribe solo lo marcado; PDF final si no hay cambio de pago.
5. Visto de contabilidad escribe `payment_mode_id` y PDF con Área Financiera.
6. Denegar desde enviada no escribe; denegar desde visto académico no revierte lo académico ni escribe pago.
7. RPC: académico no puede el visto financiero; contabilidad no puede crear.
8. Tests de módulo GREEN en `docker-compose.local.yml`; E2E TestSprite o skip justificado.
