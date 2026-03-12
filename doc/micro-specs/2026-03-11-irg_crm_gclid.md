# Micro-spec: irg_crm_gclid

1. Title: Add `x_gclid` to `crm.lead`
2. Summary: Añade un campo `x_gclid` a las oportunidades (`crm.lead`) para almacenar GCLID.
3. Justification: Necesidad de rastrear GCLID en leads sin tocar core; módulo extra en `addons-extra/extrairg`.
4. Scope: Añade campo en Python (`models/crm_lead.py`). No vistas ni datos.
5. Design: Hereda `crm.lead` con `_inherit` y define `x_gclid = fields.Char(...)`.
6. Depends: `crm` (en `__manifest__`).
7. Backwards compatibility: Campo nuevo, no rompe datos existentes.
8. Tests / Acceptance: Campo accesible desde UI en modo desarrollador; puede leerse/escribirse vía ORM.
9. Rollback: Desinstalar módulo o eliminar campo manualmente.
10. Estimation / Responsible: 15 min. Responsible: iRG dev.
