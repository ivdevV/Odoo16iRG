# Changelog — irg-practice-agreement-specific-national

## 16.0.1.1.0 — 2026-09-07

- **Excepción autorizada:** el específico nacional se añade en
  `irg_practice_agreement_specific`, no en un módulo nuevo. Un addon
  hermano solo para esta variante duplicaría wizard, doble firma y PDF.
  No se tocan `irg_practice_agreement_sign` ni
  `irg_practice_agreement_types`.
- Radio del wizard: Internacional / Nacional.
- Plantilla nacional genérica: seguros a cargo de iRG, ley 26/2015;
  sin «fuera de España» ni datos del ejemplo.
- Mismos predicados Python/QWeb para ambos específicos; filename
  `Convenio_Especifico_Nacional_...`.
