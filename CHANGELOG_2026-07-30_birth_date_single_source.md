# 2026-07-30 — Fecha de nacimiento: fuente única y fin de las fechas inventadas

## El problema

La fecha de nacimiento vivía en **dos columnas independientes**, `res.partner.birth_date` y
`op.student.birth_date`, sincronizadas solo por copias sueltas repartidas por cuatro módulos.
Cuando alguna de esas copias no encontraba valor, **escribía una fecha inventada** para poder
guardar, porque `op.admission.birth_date` era `required=True`.

Dos valores fabricados distintos, ambos localizados en producción:

- `01/01/2000` — cinco fallbacks en `irg_sale_manual_confirmation_wizard` e
  `isep_admission_from_student_field`.
- La **fecha de creación del propio registro** — el antiguo `fields.Date.today()` que el
  changelog del 22 de julio dice haber retirado, pero cuyos datos dañados seguían ahí.

Ninguno de los dos se distingue de un dato real mirando la ficha. Y peor: como los fallbacks
iban dentro de un `if not birth_date`, una vez escrito el valor falso la condición ya no volvía
a cumplirse y **el error nunca se autocorregía**.

### Alcance del daño medido en producción (978 alumnos)

| Situación | Alumnos |
|---|---|
| Fecha correcta en alumno y contacto | 637 (65%) |
| Recuperable copiando del contacto | 51 |
| Recuperable copiando del alumno | 6 |
| **Sin fecha real en ningún sitio de Odoo** | **284 (29%)** |

## La solución

Módulo nuevo `addons-extra/extrairg/irg_birth_date_single_source`:

- **`op.student.birth_date` pasa a ser `related='partner_id.birth_date'` almacenado y editable.**
  Como `op.admission.birth_date` ya era related al mismo sitio, los tres campos pasan a ser
  **el mismo dato**: divergir se vuelve imposible por construcción, y editar desde la ficha del
  alumno o desde la del contacto es equivalente.
- **`op.admission.birth_date` deja de ser obligatorio.** Era la causa raíz: el código inventaba
  fechas porque sin ellas no podía guardar.
- **Campo `irg_birth_date_missing`** y filtro *Sin fecha de nacimiento* en el listado de alumnos,
  que detecta los tres casos: vacío, `01/01/2000` y fecha igual a la de creación.

Y en los módulos que fabricaban las fechas, se eliminan los cinco fallbacks: ahora, si no hay
fecha real, el campo queda **vacío** y se deja un `WARNING` en el log.

### Dos detalles que no son obvios

**`store=True` no es una preferencia, es obligatorio.** Hay informes que leen
`op_student.birth_date` con SQL crudo (`isep_control_escolar/models/student_report.py:66`). Con
`store=False` la columna se quedaría congelada y esos informes mentirían en silencio.

**Odoo no recalcula una columna preexistente al convertirla en related almacenado**: solo computa
las filas cuyo valor es `NULL`. Sin un `post_init_hook`, las divergencias antiguas sobrevivirían a
la instalación. Verificado empíricamente: en la primera versión del módulo, sin ese hook, el caso
"contacto bueno / alumno corrupto" quedaba sin arreglar.

## Migración de datos

1. **`pre_init_hook`** — sube al contacto la fecha buena que solo exista en la ficha del alumno.
   Tiene que correr **antes** de la conversión: en cuanto el campo es related, el contacto manda,
   y esos valores se perderían.
2. **`post_init_hook`** — alinea la columna del alumno con la del contacto.

Los registros sin fecha recuperable **no se tocan ni se rellenan con nada**: quedan listados en
el filtro para que administración los pida de nuevo.

## Validación

- 14/14 tests del módulo nuevo verdes.
- Migración probada sembrando en local los cinco patrones observados en producción: control,
  rescatable, recomputable, irrecuperable y contacto vacío. Los cinco quedan consistentes y el
  irrecuperable se marca sin inventar nada.
- Regresión de los dos módulos editados: **9 errores de 16 tests antes y después**, medido
  comparando contra el código original con `git stash`. Esos 9 son preexistentes (el `setUp` no
  puede crear `op.course`) y no tienen relación con la fecha de nacimiento.

## Pendiente

- Los **284 alumnos sin fecha recuperable** necesitan que se les vuelva a pedir el dato. El
  filtro los lista.
- La conversión se ha probado en local sobre datos sembrados. Antes de producción conviene
  ensayarla sobre una copia real de `Base16`, donde son 978 alumnos y no 5.
