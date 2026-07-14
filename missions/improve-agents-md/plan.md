# Plan de misión: improve-agents-md

## Alcance

Reescribir de forma focalizada `AGENTS.md` según `spec.md`, sin cambiar código Odoo, despliegue ni módulos existentes.

## Complejidad

- Tier: `standard`.
- Señales: un archivo de política funcional, sin código de negocio ni cambios de seguridad efectivos, pero con decisiones operativas que afectan a futuros flujos.
- Los artefactos de misión no cuentan para clasificar la complejidad funcional.

## Fases

1. Diseño aprobado y especificado en `spec.md`.
2. Implementación por subagente documentador/editor sobre `AGENTS.md`.
3. Review independiente de contradicciones, placeholders y ejecutabilidad.
4. Validación estructural y semántica con `verification.json` válido.
5. Documentación final de cambios y aprendizaje reutilizable solo si aporta información no contenida en la propia política.

## Restricciones

- Preservar la prohibición de push sin autorización explícita nueva.
- No tocar cambios locales del checkout principal.
- No publicar ni crear PR como parte de esta misión sin una petición posterior.

