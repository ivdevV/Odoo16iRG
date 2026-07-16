# IRG Diploma Gradebook Template Authoritative

## Propósito y problema real

`irg_diploma_gradebook_template_authoritative` hace que la selección explícita
de la plantilla `Diplomado - Solo examen - Ponderación 50/50` sea la autoridad
del promedio final de una libreta de Diplomado.

El problema observado en beta no era un selector equivocado. `gradebook_id` es
el campo correcto, pero el comportamiento heredado de `app.gradebook.student`
ya calcula `total_final` y `avg_score` a partir de las notas finales de las
asignaturas obligatorias, incluso cuando no se ha seleccionado una plantilla.
Por eso el promedio `9,78` aparecía antes de elegirla y podía mantenerse al
cambiarla: era una media válida producida por el cálculo base, no evidencia de
que la plantilla estuviera ponderando el total.

Además, las plantillas estándar organizan evaluaciones dentro de cada
asignatura. En la implementación heredada del proyecto, cambiar entre `Solo
examen` y `Examen y asignación` no garantiza por sí mismo una fórmula distinta
para el promedio global. La ponderación presencial/resto es una regla adicional
que se activa únicamente con el modo especial `diploma_50_50`.

## Arquitectura

El addon es un puente de herencia y no modifica módulos existentes. Extiende
`app.gradebook.student` mediante `_inherit` y no crea modelos, campos, vistas ni
permisos nuevos.

Su comportamiento se divide en tres partes:

1. `_get_diploma_weighting_values()` considera autoritativo
   `gradebook_id.final_calculation_mode == 'diploma_50_50'`. Cuando el usuario
   selecciona ese modo no consulta categoría, tipo ni nombre del curso, porque
   esas clasificaciones son inconsistentes en beta.
2. `_amount_prod_final()` y `compute_avg_score()` ejecutan primero `super()` y
   reaplican al final el resultado especial. Así se conserva la cadena MRO y se
   evita que un compute heredado deje de nuevo la media simple.
3. `write()` detecta cambios de `gradebook_id`, invalida `total_final` y
   `avg_score`, y ejecuta ambos cálculos inmediatamente. Una clave de contexto
   evita reentradas futuras en esa cadena.

Las dependencias declaradas de los computes incluyen el selector, su modo de
cálculo, las notas finales y los datos que identifican las asignaturas. El
helper conserva la fuente heredada de exenciones NLEX/EX mediante
`irg_is_grade_exempt()`.

## Dependencias

El addon depende directamente de:

- `irg_diploma_gradebook_beta_course_detection`.

Esa dependencia incorpora transitivamente la cadena previa de ponderación
50/50, compatibilidad NLEX/EX y detección de Diplomados. No se deben desinstalar
los addons anteriores mientras este módulo esté instalado.

## Instalación en beta

1. Desplegar el código que contiene
   `irg_diploma_gradebook_template_authoritative`.
2. Actualizar la lista de aplicaciones en modo desarrollador si el addon no
   aparece.
3. Quitar el filtro `Aplicaciones` si impide ver módulos técnicos.
4. Buscar e instalar `IRG Diploma Gradebook Template Authoritative`.
5. Abrir la libreta en `app.gradebook.student`.
6. Si la libreta ya tenía seleccionada la plantilla especial antes de instalar
   el addon, cambiar temporalmente a una plantilla estándar, guardar, volver a
   seleccionar `Diplomado - Solo examen - Ponderación 50/50` y guardar.

No hay migración ni recálculo masivo de libretas históricas. El recálculo
explícito se dispara cuando cambia `gradebook_id`.

## Uso y resultado esperado

La plantilla debe mostrar:

```text
Cálculo final: Diplomado: presencial 50% + resto 50%
```

La fórmula es:

```text
final = nota_presencial * 0,50
      + promedio(módulos ordinarios obligatorios no exentos) * 0,50
```

Caso de beta validado:

```text
presencial = 8,44
ordinarios = 10, 10, 10, 10, 10, 10
media base = 9,78
50/50      = 8,44 * 0,50 + 10 * 0,50 = 9,22
```

Al guardar el cambio desde una plantilla estándar a la especial, tanto
`Promedio total` (`total_final`) como `avg_score` deben pasar inmediatamente de
`9,78` a `9,22`. Las plantillas estándar siguen usando el comportamiento
heredado.

## Validaciones funcionales

Para aplicar el modo especial deben existir:

- exactamente una asignatura obligatoria identificada como módulo presencial;
- al menos una asignatura obligatoria ordinaria no exenta; y
- la selección explícita del modo `diploma_50_50`.

Las asignaturas NLEX/EX continúan fuera del cálculo. Si hay cero o más de un
presencial, o no existen módulos ordinarios válidos, el addon registra una
advertencia y conserva de forma segura el cálculo heredado.

## Pruebas

La validación se ejecutó con `docker-compose.local.yml` en la base aislada
`test_irg_diploma_authoritative_v2_20260715`. Odoo instaló el addon como módulo
231/231 y ejecutó cinco pruebas `TransactionCase` post-install:

- el modo especial produce `9,22` aunque el detector heredado de Diplomado sea
  forzado a falso y confirma que dicho detector no se consulta;
- cambiar de plantilla recalcula inmediatamente `9,78` a `9,22`;
- una plantilla estándar conserva `9,78`;
- una asignatura NLEX con nota `1` no cambia el resultado `9,22`; y
- dos candidatos presenciales desactivan el modo especial y conservan el
  fallback heredado.

Resultado: 5 pruebas superadas, 0 fallos y 0 errores; 825 consultas en 0,76
segundos. También pasaron la instalación de Odoo, el parseo AST de seis
archivos Python, manifest, imports, inventario de tests y revisión de espacios.
El proceso Odoo terminó con código 0.

## Limitaciones conocidas

- Solo modifica la ponderación global del modo `diploma_50_50`; no cambia cómo
  una plantilla estándar combina exámenes y asignaciones dentro de cada
  asignatura.
- Requiere exactamente un módulo presencial obligatorio y al menos un módulo
  ordinario obligatorio no exento.
- Depende de los contratos internos `_get_diploma_final_score()`,
  `_is_presential_module_subject()` e `irg_is_grade_exempt()` de la cadena de
  addons previa.
- No corrige categorías, tipos ni nombres de cursos almacenados.
- No ejecuta migraciones ni recálculos masivos de libretas históricas.
- Una libreta que ya tenía la plantilla especial al instalar el addon puede
  requerir volver a cambiar y guardar `gradebook_id` para disparar el recálculo
  explícito.

## Changelog

### 16.0.1.0.0 — 2026-07-15

- Convertido el modo seleccionado `diploma_50_50` en autoridad funcional del
  cálculo, sin depender de la clasificación secundaria del curso.
- Reaplicado el resultado 50/50 al final de los computes de `total_final` y
  `avg_score`.
- Añadido recálculo inmediato al cambiar `gradebook_id`.
- Conservadas las exenciones NLEX/EX y el fallback seguro ante una estructura
  ambigua de asignaturas.
- Añadidas cinco pruebas de regresión e integración.
