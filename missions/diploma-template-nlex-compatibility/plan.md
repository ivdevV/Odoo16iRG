# Plan: compatibilidad ponderación 50/50 con NLEX

## Objetivo

Corregir el conflicto de herencia entre
`irg_diploma_gradebook_template_weighting` e `irg_nlex_grade_exemption` para
que la plantilla especial calcule 50 % del módulo presencial y 50 % del
promedio de los demás módulos obligatorios, sin alterar cursos que no sean
diplomados ni las exclusiones NLEX.

## Evidencia del problema

- Caso reproducido: seis módulos con 10 y módulo presencial con 8,44.
- Resultado observado: 9,78, que corresponde a la media simple
  `(6 * 10 + 8,44) / 7`.
- Resultado esperado: 9,22, calculado como `(10 * 0,5) + (8,44 * 0,5)`.
- `irg_nlex_grade_exemption` redefine `_amount_prod_final` y
  `compute_avg_score` sin encadenar `super()`, por lo que puede sobrescribir la
  ponderación especial según el orden de carga de módulos.

## Alcance

1. Crear un addon nuevo en `addons-extra/extrairg/` que dependa explícitamente
   de los módulos de ponderación por plantilla y de exclusión NLEX.
2. Extender `app.gradebook.student` mediante `_inherit`.
3. Ejecutar primero el cálculo heredado y aplicar después el resultado especial
   devuelto por `_get_diploma_final_score()` cuando corresponda.
4. Conservar el resultado heredado para plantillas estándar, cursos no
   diplomados y configuraciones donde la regla 50/50 no sea válida.
5. Añadir pruebas de regresión para el caso 9,22, cursos no diplomados y
   exclusiones NLEX.

## Fuera de alcance

- Modificar módulos existentes.
- Cambiar la definición funcional de `survey_type = exam`.
- Modificar datos históricos o ejecutar migraciones.
- Hacer commit o push sin autorización posterior del usuario.

## Complejidad y routing

- **Tier:** `complex`.
- **Justificación objetiva:** aunque la lógica es acotada, el cambio requiere
  un addon nuevo con más de cinco archivos y valida interacción cross-module y
  orden de herencia Odoo.
- **Implementación:** subagente codificador de alta capacidad.
- **Validación:** subagente testeador; pruebas Odoo mediante
  `docker-compose.local.yml` cuando el runtime esté disponible.
- **Documentación:** subagente documentador ligero después de una verificación
  `passed`.
- **Security Advisor:** no aplica; no se tocan autenticación, secretos,
  despliegue, concurrencia, migraciones ni borrado de datos.

## Validación prevista

- Instalación/actualización del addon en Odoo 16 local.
- Test de integración con ambos módulos instalados:
  seis notas 10 y presencial 8,44 producen `total_final = avg_score = 9,22`.
- Plantilla estándar conserva media simple.
- Curso no diplomado conserva comportamiento estándar.
- Asignaturas NLEX continúan excluidas.
- Python/manifest/XML, lint disponible y `git diff --check`.

## Conocimiento aplicado

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`:
  addon bajo `addons-extra/extrairg/`, prefijo `irg_`, herencia Odoo y ausencia
  de modificaciones directas a módulos existentes.
