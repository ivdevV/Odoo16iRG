# Ejecución — irg_oral_case

## 2026-10-22 — Plan

- Rama de trabajo: `cursor/irg-oral-case-ed40`, creada desde `Dev_iRG` (`f2c29242f`).
- `PROJECT.md` pide `feat/<misión>`. Esta ejecución en cloud exige el prefijo `cursor/` y el sufijo `-ed40`. Se documenta en la PR; la base y el destino del PR siguen siendo `Dev_iRG`.
- No existe `docker-compose.local.yml` en el repo. `docker info` falla en esta VM (no hay daemon). No hay binario `odoo`. Python del host: 3.12.3.
- TDD con el runtime Odoo no es ejecutable aquí antes de codificar. Causa: sin Docker, sin compose local y sin código fuente de `website_slides` (no está vendorizado; OpenEduCat sí). Alternativa de verificación: `python3 -m py_compile` y parseo XML de los archivos del módulo, más lectura de los tests. Los tests de Odoo quedan escritos para el comando canónico y no se marcan como pasados si no se ejecutan.
- Security Advisor del diseño: `[YES]` en `artifacts/security-advisor.txt`, antes del código de producto.

## 2026-10-22 — Implementación, review y validación

- Código en `addons-extra/extrairg/irg_oral_case`. No se editó ningún módulo existente.
- `python3 -m py_compile` y el parseo de los 8 XML: exit 0. Evidencia en `artifacts/syntax.txt`.
- Tests de Odoo no ejecutados. `docker` no está instalado (exit 127). No hay `docker-compose.local.yml` ni binario `odoo`. Causa registrada en el plan antes de codificar y repetida aquí. No se marca el check como pass.
- TestSprite no está entre los MCP de este runtime. El disparo E2E se mantiene. Check `e2e_testsprite` = `skipped`. No se llamó a beta ni a producción.
- Review de código: `artifacts/02-review.md`, sin bloqueantes.
- Security Advisor del código: `[YES]` en `artifacts/security-advisor-code.txt`.
- Documentación: `README.md` del módulo, `doc/modules/extrairg/irg_oral_case.md`, `CHANGELOG_2026-10-22_irg_oral_case.md` y knowledge `irg_oral_case.md`.

## Decisiones

- Nombre del módulo: `irg_oral_case`.
- No se cambia el tipo del slide.
- No se depende de `dv_slide_channel_custom`. Los campos IA se redefinen con el mismo nombre técnico.
- La nota oficial no pasa por `survey.user_input.result_id`.
