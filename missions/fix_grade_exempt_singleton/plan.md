# Misión: fix_grade_exempt_singleton

## Alcance y Objetivos
- Corregir el error `ValueError: Expected singleton: op.subject()` que ocurre al intentar acceder a la libreta de calificaciones cuando una materia obligatoria tiene el campo `op_subject_id` vacío o no establecido.
- Resolver el conflicto de inicialización de la suite de pruebas debido a incompatibilidades de género en `res.partner`.
- Validar los cambios con pruebas unitarias locales usando `docker-compose.local.yml`.

## Clasificación de Complejidad
- **Tier:** `standard` (2-5 archivos afectados, fix localizado, sin cambios en base de datos ni riesgos de seguridad).

## Modelos y Subagentes Utilizados
- **Fase de Plan:** Orquestador (Reasoning model).
- **Fase de Implementación:** Codificador (Subagente `self` o directo).
- **Fase de Validación:** Testeador (Subagente `self` o directo).
- **Fase de Documentación:** Documentador (Subagente `self` o directo).

## Plan de Implementación
1. Modificar `irg_is_grade_exempt` en `addons-extra/extrairg/irg_nlex_grade_exemption/models/op_subject.py` para devolver `False` si el recordset está vacío.
2. Añadir `irg_admission_gender_fix` como dependencia en `addons-extra/extrairg/irg_nlex_grade_exemption/__manifest__.py`.
3. Añadir caso de prueba en `addons-extra/extrairg/irg_nlex_grade_exemption/tests/test_nlex_grade_exemption.py` que valide el comportamiento con recordsets vacíos.
4. Ejecutar pruebas unitarias locales y registrar resultados.
