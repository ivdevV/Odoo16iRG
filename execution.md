# Execution Log: Módulo de Convenios de Prácticas y Firma Digital (`irg_practice_agreement_sign`)

## Fase 1: Plan
- Creado `plan.md` y `implementation_plan.md`.
- Analizados los documentos `Convenio Marco iRG - Modelo firma.docx`, `Convenio Marco iRG - Modelo firma.pdf` y `Firma Raimon.png`.

## Fase 2: Implementación y TDD
- [ ] Crear estructura del módulo `addons-extra/extrairg/irg_practice_agreement_sign`.
- [ ] Copiar `Firma Raimon.png` a `static/src/img/firma_raimon.png`.
- [ ] Escribir modelos `practice.agreement` y extensión de `practice.center`.
- [ ] Escribir controlador portal `/convenio/firma/<token>`.
- [ ] Diseñar vista web portal con canvas de firma táctil.
- [ ] Diseñar reporte QWeb PDF con las 8 cláusulas del convenio e imágenes de firmas.
- [ ] Escribir pruebas unitarias en `tests/test_practice_agreement.py`.
- [ ] Ejecutar pruebas.

## Fase 3: Review de código
- Requisito de revisor independiente / comprobación antipatrones.

## Fase 4: Validación
- Generar `verification.json` con resultados de tests.

## Fase 5: Documentación
- Actualizar `CHANGELOG.md`.

## Fase 6: Publicación Autorizada
- Git commit y push a `Dev_iRG` según autorización explícita del usuario.
