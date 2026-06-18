# Micro-spec: irg_diploma_gradebook_weighting
**Fecha:** 2026-06-18  
**Modulo:** `irg_diploma_gradebook_weighting`  
**Ruta:** `addons-extra/extrairg/irg_diploma_gradebook_weighting/`

---

## 1. Titulo corto
Ponderacion 50/50 y recuperacion general para libretas de Diplomado.

## 2. Resumen objetivo
Aplicar una formula especifica de calificacion final en cursos tipo Diplomado: 50% corresponde al subject `Módulo Presencial` y 50% corresponde al promedio de los demas modulos obligatorios no presenciales. Si el resultado base es inferior a 7, se habilita una recuperacion general cuya nota sustituye la nota final con maximo permitido de 7.

## 3. Motivo / justificacion
Los diplomados necesitan una regla de cierre academico distinta a la media estandar de la libreta. La ponderacion debe mantener fijo el peso del bloque no presencial aunque varie el numero de modulos, y debe permitir una recuperacion unica cuando el resultado base no alcanza el umbral minimo.

## 4. Alcance exacto
- Herencia de `app.gradebook.student`.
- Nuevos campos almacenados para control de recuperacion de diplomado:
  - `diploma_recovery_required`
  - `diploma_recovery_score`
  - `diploma_recovery_applied`
- Sobrescritura conservadora de los calculos finales `total_final` y `avg_score` solo cuando aplica la regla de Diplomado.
- Extension de la vista formulario de libreta para mostrar el bloque "Recuperacion diplomado".
- Tests `TransactionCase` incluidos en el modulo para cubrir reglas principales, aunque no ejecutados en runtime local durante esta fase.

## 5. Reglas de negocio
- Aplica solo a cursos cuyo `op.course.course_type_id` identifica Diplomado.
- La identificacion contempla nombre normalizado `Diplomado` / `Diplomados` o codigo que empieza por `DIP`.
- Requiere un subject llamado `Módulo Presencial` en la libreta del alumno para activar la formula especial.
- Solo se consideran modulos obligatorios (`subject_type = compulsory`).
- Nota base final = 50% `Módulo Presencial` + 50% promedio de los otros modulos obligatorios no presenciales.
- El numero de modulos no presenciales puede variar; su promedio completo siempre representa el bloque del 50%.
- Si la nota base final es menor que 7, se requiere y habilita una unica recuperacion general.
- La nota de recuperacion sustituye la nota final y la media final, con nota maxima permitida de 7.
- Las notas de recuperacion negativas no estan permitidas.
- Los no diplomados y los diplomados sin `Módulo Presencial` conservan el comportamiento estandar de la libreta.

## 6. Diseno tecnico
### Dependencias
```python
[
    'isep_gradebook',
    'isep_control_escolar',
    'isep_student_migration',
]
```

### Modelo heredado
`app.gradebook.student` calcula internamente los valores de diplomado mediante helpers privados:
- `_get_diploma_weighting_values()` devuelve la nota presencial, el promedio no presencial y la nota base.
- `_get_diploma_final_score()` devuelve `False` si no aplica; si aplica recuperacion, devuelve `min(diploma_recovery_score, 7.0)`; si no, devuelve la nota base.
- `_is_diplomado_course()` normaliza nombre y codigo del tipo de curso.
- `_is_presential_module_subject()` normaliza el nombre del subject para reconocer `Módulo Presencial`.

### Vista
La vista `views/app_gradebook_student_views.xml` inserta un grupo despues de `//group[@name='average_final']` con:
- Indicador de recuperacion requerida.
- Indicador de recuperacion aplicada.
- Campo editable `diploma_recovery_score` cuando la recuperacion esta requerida.

## 7. Backwards-compatibility / migracion
- No modifica tablas core ni reemplaza vistas base.
- Los campos nuevos se agregan sobre `app.gradebook.student`.
- La logica llama primero al comportamiento estandar mediante `super()` y solo reemplaza `total_final` / `avg_score` cuando el curso y la libreta cumplen las condiciones de Diplomado.
- Los registros existentes de no diplomados o diplomados sin `Módulo Presencial` deben conservar su calculo previo.

## 8. Casos de prueba / criterios de aceptacion
1. Diplomado con `Módulo Presencial` y seis modulos obligatorios no presenciales aplica ponderacion 50/50.
2. Diplomado con cantidad variable de modulos no presenciales mantiene el bloque no presencial como 50%.
3. Curso no Diplomado conserva la media estandar.
4. Diplomado sin `Módulo Presencial` conserva la media estandar.
5. Diplomado con nota base inferior a 7 marca recuperacion requerida.
6. Nota de recuperacion valida sustituye `total_final` y `avg_score`.
7. Nota de recuperacion mayor que 7 lanza `ValidationError`.

## 9. Validacion documentada
Evidencia ligera reportada como pasada:
- Estructura de modulo.
- Manifest.
- Compilacion Python de 6 archivos.
- Parseo XML.
- IDE lints.
- Checks estaticos Odoo.

Validacion completa pendiente:
- Los tests Odoo `TransactionCase` no se ejecutaron porque no habia runtime local disponible.
- No se encontro `docker-compose.local.yml`.
- No habia comando local `odoo`.
- El daemon de Docker no estaba en ejecucion.

## 10. Rollback
```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <db> \
  --uninstall-modules irg_diploma_gradebook_weighting --stop-after-init --db_host=pgodoo_latest
```
Eliminar carpeta `addons-extra/extrairg/irg_diploma_gradebook_weighting/` si se revierte el despliegue del modulo.

## 11. Changelog
- 2026-06-18: Documentada la micro-spec del modulo `irg_diploma_gradebook_weighting`, incluyendo reglas de negocio, diseno tecnico, criterios de aceptacion, evidencia de validacion ligera y limitacion por falta de runtime Odoo local.
