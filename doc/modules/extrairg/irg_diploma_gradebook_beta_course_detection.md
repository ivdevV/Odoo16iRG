# IRG Diploma Gradebook Beta Course Detection

## Propósito

`irg_diploma_gradebook_beta_course_detection` corrige la detección de
Diplomados en bases como beta donde el nombre del curso es inequívoco, pero su
tipo o categoría de producto conserva una clasificación heredada que no
corresponde a un Diplomado.

El síntoma observado era que, aun seleccionando y guardando varias veces la
plantilla `Diplomado - Solo examen - Ponderación 50/50`, la libreta mantenía la
media simple `9,78`. Para seis módulos ordinarios con nota `10` y un módulo
presencial con `8,44`, el resultado correcto es `9,22`.

## Arquitectura

El addon no crea modelos, campos, vistas ni reglas de acceso. Extiende mediante
`_inherit` el modelo `app.gradebook.student` y redefine únicamente
`_is_diplomado_course()`.

La detección sigue este orden:

1. Ejecuta `super()` y conserva todos los criterios estructurados existentes.
2. Solo si la detección heredada falla, normaliza el nombre del curso.
3. Acepta `Diplomado` o `Diplomados` cuando aparece al inicio del nombre o
   inmediatamente después del separador ` - `.

Ejemplos válidos:

- `Diplomado en Terapias de Tercera Generación`;
- `TG - Diplomado en Terapias de Tercera Generación`.

Un nombre como `Curso en Terapias de Tercera Generación` no coincide. Además,
la regla 50/50 conserva su segunda barrera: la libreta debe tener seleccionada
explícitamente la plantilla cuyo modo es `diploma_50_50`.

## Dependencias

El addon depende de:

- `irg_diploma_gradebook_template_nlex_compat`.

Esa dependencia asegura que se cargue después del puente que compatibiliza la
ponderación de Diplomados con la exclusión NLEX/EX. Transitivamente también se
requieren el addon de la plantilla 50/50 y `irg_nlex_grade_exemption`.

## Instalación o actualización en beta

1. Incorporar el addon al código desplegado en beta.
2. Actualizar la lista de aplicaciones si el módulo todavía no aparece.
3. Instalar `IRG Diploma Gradebook Beta Course Detection` o actualizarlo si ya
   está instalado.
4. Abrir la libreta y seleccionar
   `Diplomado - Solo examen - Ponderación 50/50`.
5. Guardar la libreta y comprobar el promedio total.

No se debe desinstalar `irg_diploma_gradebook_template_weighting` ni
`irg_diploma_gradebook_template_nlex_compat`: son dependencias funcionales del
nuevo addon. No hay migración ni escritura masiva de datos históricos.

## Uso y cálculo esperado

La plantilla especial se aplica únicamente cuando se cumplen ambas
condiciones:

- el curso se reconoce como Diplomado por su clasificación estructurada o por
  el patrón inequívoco de su nombre; y
- la libreta usa el modo `diploma_50_50`.

El cálculo heredado permanece:

```text
final = presencial * 0,50 + promedio(ordinarios no exentos) * 0,50
```

Caso validado en la regresión de beta:

```text
presencial = 8,44
ordinarios = 10, 10, 10, 10, 10, 10
final      = 8,44 * 0,50 + 10 * 0,50 = 9,22
```

Con un template estándar, ese mismo conjunto conserva temporalmente la media
simple `9,78`; al cambiar al template especial se recalcula a `9,22`.

## Pruebas

La validación se ejecutó con `docker-compose.local.yml` en la base aislada
`test_irg_diploma_beta_detect_20260715`. Odoo instaló el addon como módulo
230/230 y ejecutó tres pruebas `TransactionCase` post-install:

- categoría y tipo inconsistentes, pero nombre de Diplomado: resultado `9,22`;
- cambio de template estándar a especial: `9,78` a `9,22`;
- curso no-Diplomado con template especial: conserva `9,78`.

Resultado: 3 pruebas superadas, 0 fallos y 0 errores; 568 consultas en 0,87
segundos. También pasaron compilación AST de seis archivos Python, manifest,
imports, presencia de dependencias, `git diff --check`, configuración del
compose e instalación de Odoo.

## Limitaciones conocidas

- La detección alternativa depende del nombre del curso y solo admite el patrón
  inequívoco descrito; no intenta inferir abreviaturas o menciones ambiguas.
- No corrige la categoría o el tipo académico almacenados en el curso.
- No modifica notas por asignatura, `survey_type` ni la identificación del
  módulo presencial.
- No fuerza un recálculo masivo de libretas históricas.
- Depende de los contratos internos de los addons de ponderación y
  compatibilidad NLEX.

## Changelog

### 16.0.1.0.0 — 2026-07-15

- Añadida detección de Diplomados por nombre cuando la clasificación de beta es
  inconsistente.
- Conservada la detección estructurada heredada mediante `super()`.
- Protegidos templates estándar y cursos no-Diplomado mediante pruebas de
  regresión.
- Validado el recálculo de `9,78` a `9,22` al seleccionar el template 50/50.
