# Changelog 2026-04-15

- Módulo: `irg_portal_placeholder_count_fix`
- Problema: error JS en el portal al renderizar badges con `data-placeholder_count` cuando el valor de contador no estaba presente.
- Solución: override de `portal.CustomerPortal._prepare_home_portal_values` que garantiza valores por defecto `0` para los placeholders de contador solicitados y para los keys conocidos de documentos y pedidos.
- Validación: prueba de `TransactionCase` que confirma el fallback correcto.
