# IRG Diploma Gradebook Template NLEX Compatibility

## Propósito

`irg_diploma_gradebook_template_nlex_compat` compatibiliza la ponderación final
de Diplomados con la exclusión de asignaturas NLEX/EX. Corrige el caso donde
un override compute sin `super()` dejaba la media simple `9,78` en lugar de
`9,22` para una nota presencial `8,44` y seis módulos ordinarios con `10`.

## Arquitectura y MRO

El addon no crea modelos ni campos. Extiende `app.gradebook.student` y depende
explícitamente de:

- `irg_diploma_gradebook_template_weighting`;
- `irg_nlex_grade_exemption`.

Ese orden topológico registra el puente después de ambos addons. Sus métodos
`_amount_prod_final()` y `compute_avg_score()` ejecutan primero `super()` para
conservar el cálculo heredado. Después consultan `_get_diploma_final_score()`
y solo reaplican el resultado cuando la regla especial es válida. Si el helper
devuelve `False`, se mantiene intacta la media heredada.

El helper `_get_diploma_weighting_values()` filtra primero los subjects donde
`irg_is_grade_exempt()` es verdadero. Luego exige un único módulo presencial y
promedia los módulos obligatorios ordinarios restantes.

## Instalación y configuración

Instalar `irg_diploma_gradebook_template_nlex_compat`. Odoo resolverá sus dos
dependencias antes del puente.

No añade opciones de interfaz. Para usar la regla:

1. Seleccionar `Diplomado - Solo examen - Ponderación 50/50` en la libreta.
2. Verificar que el curso esté clasificado como Diplomado.
3. Mantener exactamente un subject obligatorio que identifique el presencial.
4. Usar el marcador de código `EX` para subjects exentos, incluida la familia
   `NLEX`, conforme al contrato de `irg_nlex_grade_exemption`.

## Cálculo

```text
final = presencial * 0,50 + promedio(ordinarios no exentos) * 0,50
```

Caso validado:

```text
presencial = 8,44
ordinarios = 10, 10, 10, 10, 10, 10
NLEX       = excluido
final      = 8,44 * 0,50 + 10 * 0,50 = 9,22
```

Templates estándar, cursos no-Diplomado y configuraciones ambiguas conservan
el cálculo heredado filtrado por NLEX.

## Pruebas

La validación se ejecutó con `docker-compose.local.yml` en la base aislada
`test_irg_diploma_nlex_compat_20260715`. Odoo instaló el addon, cargó 229
módulos y ejecutó cuatro pruebas `TransactionCase` post-install:

- regresión `8,44 + seis notas 10 = 9,22` en `total_final` y `avg_score`;
- template estándar conserva la media heredada;
- curso no-Diplomado conserva la media heredada con el template especial; y
- un NLEX puntuado queda fuera del bloque ordinario 50 %.

Resultado: 4 pruebas superadas, 0 fallos y 0 errores. También pasaron la
compilación AST de seis archivos Python, manifest/imports, instalación y
`git diff --check`.

## Limitaciones conocidas

- Depende de los contratos internos `_get_diploma_final_score()`,
  `_get_diploma_weighting_values()` e `irg_is_grade_exempt()`.
- Requiere exactamente un presencial obligatorio y al menos un módulo
  ordinario obligatorio no exento.
- La exención coincide con cualquier código que contenga `EX`, no solo `NLEX`.
- No migra datos históricos ni fuerza recálculos masivos.
- No sustituye la configuración del template ni la clasificación del curso.

## Changelog

### 16.0.1.0.0 — 2026-07-15

- Añadido puente final para `total_final` y `avg_score`.
- Conservado el cálculo heredado para casos no aplicables.
- Excluidos NLEX/EX antes de formar el bloque ordinario 50 %.
- Añadidas cuatro pruebas de integración y regresión.
