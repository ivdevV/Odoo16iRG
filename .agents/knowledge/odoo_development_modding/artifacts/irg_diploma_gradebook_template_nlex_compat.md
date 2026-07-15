# Compatibilidad de campos calculados entre addons Odoo

## Contexto

`irg_diploma_gradebook_template_weighting` aplica una ponderación 50/50 a
Diplomados, mientras `irg_nlex_grade_exemption` excluye asignaturas cuyo código
contiene `EX`. Ambos addons redefinen los cálculos `total_final` y `avg_score`.

## Gotcha descubierto

Un override de un método compute que no llama a `super()` puede cortar la
cadena MRO y reemplazar silenciosamente el resultado de otro addon. El síntoma
fue una media simple de 9,78 en lugar del resultado especial 9,22, aunque el
template correcto estaba seleccionado y las notas por asignatura eran válidas.

Los tests aislados de un solo addon no detectan este problema: es necesario
cargar juntos todos los módulos que redefinen el mismo método.

## Patrón aplicado

Crear un addon puente que:

1. dependa explícitamente de todos los addons en conflicto para asegurar su
   carga posterior;
2. extienda el mismo modelo mediante `_inherit`;
3. ejecute primero `super()` para conservar el comportamiento heredado; y
4. reaplique al final el resultado especial únicamente cuando su helper indique
   que la regla funcional es aplicable.

Cuando existe una exclusión transversal como NLEX, el helper especial también
debe usar la misma fuente de verdad (`irg_is_grade_exempt()`) antes de formar
sus conjuntos y promedios.

## Regresión mínima reutilizable

- Instalar simultáneamente los addons en conflicto y el puente.
- Probar el caso especial con valores que difieran claramente de la media
  estándar: seis notas 10 y presencial 8,44 deben producir 9,22, no 9,78.
- Probar template estándar y curso no aplicable para garantizar fallback.
- Probar una asignatura `EX` puntuada para asegurar que sigue excluida.

## Resultado validado

El addon `irg_diploma_gradebook_template_nlex_compat` pasó cuatro pruebas Odoo
en una base aislada: 0 fallos y 0 errores.
