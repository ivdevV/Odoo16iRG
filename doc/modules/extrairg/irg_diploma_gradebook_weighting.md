# irg_diploma_gradebook_weighting

**Categoria:** extrairg  
**Version:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Si  
**Autor:** IRG  
**Depende de:** `isep_gradebook`, `isep_control_escolar`, `isep_student_migration`

---

## Proposito

Extiende la libreta academica (`app.gradebook.student`) para aplicar una regla especial de nota final en cursos tipo Diplomado. La regla combina el subject `Módulo Presencial` con el promedio de los demas modulos obligatorios y habilita una recuperacion general cuando el resultado base queda por debajo de 7.

El modulo no cambia el comportamiento de cursos no diplomados ni de diplomados que no tengan un subject `Módulo Presencial`.

## Reglas de negocio

- Aplica solo a cursos cuyo `op.course.course_type_id` identifica Diplomado.
- El tipo de curso se reconoce por nombre normalizado `Diplomado` / `Diplomados`, por nombre que empieza por `Diplomado ` o por codigo que empieza por `DIP`.
- Requiere un subject llamado `Módulo Presencial` en la libreta del alumno para aplicar la formula especial.
- Solo participan subjects obligatorios (`subject_type = compulsory`).
- La nota base final se calcula como 50% `Módulo Presencial` + 50% promedio de los otros modulos obligatorios no presenciales.
- El numero de modulos no presenciales puede variar; su promedio siempre representa el bloque completo del 50%.
- Si la nota base final es menor que 7, se marca una recuperacion general como requerida.
- La nota de recuperacion reemplaza la nota final y la media final, con maximo permitido de 7.
- La nota de recuperacion no puede ser negativa.
- No diplomados y diplomados sin `Módulo Presencial` conservan el comportamiento estandar de `isep_gradebook`.

## Cambios de datos y modelos

### Modelo heredado

`app.gradebook.student` incorpora tres campos:

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `diploma_recovery_required` | Boolean calculado almacenado | Indica que la nota base del Diplomado es menor que 7 y requiere recuperacion. |
| `diploma_recovery_score` | Float | Nota de recuperacion general del Diplomado. Tiene tracking y validacion de rango 0-7. |
| `diploma_recovery_applied` | Boolean calculado almacenado | Indica que hay recuperacion requerida y una nota de recuperacion mayor que 0. |

### Calculo academico

El modulo mantiene primero el calculo estandar mediante `super()` y despues sustituye `total_final` y `avg_score` solo si `_get_diploma_final_score()` determina que aplica la regla de Diplomado.

Si no aplica la regla especial, el helper devuelve `False` y la libreta mantiene el resultado original.

## Vistas y flujo de usuario

La vista `views/app_gradebook_student_views.xml` hereda el formulario de `app.gradebook.student` e inserta el grupo "Recuperacion diplomado" despues del bloque de nota media/final.

Flujo esperado:

1. El usuario abre la libreta de un alumno.
2. Si el curso es Diplomado, existe `Módulo Presencial` y la nota base es inferior a 7, Odoo muestra el bloque de recuperacion.
3. El usuario registra `Nota recuperacion diplomado`.
4. Si la nota es valida, la recuperacion queda aplicada y sustituye `total_final` y `avg_score`.
5. Si la nota es mayor que 7 o negativa, se bloquea el guardado con `ValidationError`.

## Configuracion

- Instalar el modulo `irg_diploma_gradebook_weighting`.
- Verificar que el tipo de curso de los diplomados tenga nombre `Diplomado` / `Diplomados` o codigo con prefijo `DIP`.
- Verificar que las libretas de diplomado incluyan un subject obligatorio llamado exactamente `Módulo Presencial` o equivalente con acentos/espacios normalizables.
- Verificar que los demas modulos que deban entrar en el promedio no presencial sean subjects obligatorios.

No incluye menus propios ni parametros de sistema.

## Tests y validacion

El modulo incluye tests `TransactionCase` en `tests/test_diploma_gradebook_weighting.py` para:

- Ponderacion 50/50 con seis modulos.
- Ponderacion 50/50 con cantidad variable de modulos no presenciales.
- Preservacion del comportamiento estandar en no diplomados.
- Preservacion del comportamiento estandar en diplomados sin `Módulo Presencial`.
- Activacion de recuperacion cuando la nota base es menor que 7.
- Sustitucion de nota final mediante recuperacion.
- Validacion de nota maxima de recuperacion.

Validacion ligera reportada como pasada:
- Estructura de modulo.
- Manifest.
- Compilacion Python de 6 archivos.
- Parseo XML.
- IDE lints.
- Checks estaticos Odoo.

Validacion Odoo completa no ejecutada en esta fase:
- No se ejecutaron los tests `TransactionCase` porque el runtime local no estaba disponible.
- No existe `docker-compose.local.yml` en el entorno local.
- No existe comando local `odoo`.
- El daemon de Docker no estaba en ejecucion.

## Limitaciones conocidas

- La regla depende de que el curso este correctamente tipificado como Diplomado.
- La formula especial no se activa sin un subject `Módulo Presencial`.
- Si hay mas de una linea que normaliza como `Módulo Presencial`, se usa la primera como nota presencial y el resto queda fuera del promedio no presencial.
- La recuperacion es unica y general; no gestiona recuperaciones por modulo individual.
- La nota de recuperacion aplicada no puede superar 7 por regla de negocio.
- La ejecucion completa de tests Odoo queda pendiente hasta disponer de runtime local o entorno Docker operativo.

## Instalacion / actualizacion

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_diploma_gradebook_weighting \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_diploma_gradebook_weighting \
    --stop-after-init --db_host=pgodoo_latest
```

## Changelog

- 2026-06-18: Documentado el modulo `irg_diploma_gradebook_weighting` con proposito, reglas de negocio, cambios de modelo, flujo de usuario, configuracion, evidencia de validacion y limitaciones conocidas.
