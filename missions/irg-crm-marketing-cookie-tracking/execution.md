# Ejecución: cookies de atribución CRM

## Decisiones

- Los cinco identificadores se almacenan como texto libre (`Char`).
- Marketing recibe `fbc` y `fbp`; Reactivación recibe `fbclid_reactivacion`, `fbc_reactivacion` y `fbp_reactivacion`.
- TDD de instalación no es viable sin el runtime Odoo/Docker, cuya ejecución fue excluida por el usuario. Se aplicarán checks estáticos alternativos antes de publicar.

## Implementación

- Añadidos `fbc` y `fbp` a Marketing.
- Añadidos `fbclid_reactivacion`, `fbc_reactivacion` y `fbp_reactivacion` a Reactivación.

## Gates

- Revisión independiente aprobada; evidencia en `artifacts/code-review.txt`.
- Validación independiente estática aprobada; evidencia en `artifacts/static-validation.txt`.
- Docker y pruebas Odoo no ejecutados por instrucción explícita del usuario.
