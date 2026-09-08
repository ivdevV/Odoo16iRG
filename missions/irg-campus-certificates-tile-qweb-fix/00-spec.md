# Spec — irg-campus-certificates-tile-qweb-fix

Ver `docs/superpowers/specs/2026-09-04-irg-campus-certificates-tile-qweb-fix-design.md`.

Criterios de aceptación:

1. El `t-if` combinado del nodo `certificates_and_diplomas` no usa `hasattr`.
2. Usa `course_id.is_diplomado()`.
3. Renderizar esa expresión con `ir.qweb` no lanza `TypeError`.
4. En un máster el tile se muestra; en un diplomado (`code` `DI…`) no.
5. No se edita `irg_campus_certificates_portal`.
