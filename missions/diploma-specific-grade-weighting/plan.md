# Plan - diploma-specific-grade-weighting

## Objetivo

Ajustar el calculo final de las libretas de los cursos tipo Diplomado para que:

- El examen de certificacion del subject cuyo nombre identifica el modulo presencial aporte el 50% de la nota final.
- Los demas subjects obligatorios del diplomado compartan de forma equitativa el otro 50%.
- El numero de modulos no presenciales pueda variar entre diplomados sin requerir porcentajes configurados manualmente.
- Los cursos que no sean Diplomado conserven exactamente el calculo estandar de `isep_gradebook`.

## Confirmaciones del usuario

- La regla se aplicara exclusivamente a cursos tipo Diplomado; ningun otro tipo de curso debe cambiar.
- El examen de certificacion es la unica evaluacion del modulo presencial.
- Los modulos no presenciales tambien tienen una unica evaluacion de certificacion.
- La activacion se realizara mediante un nuevo template seleccionable en la libreta, combinado con una salvaguarda que exige que el curso sea realmente un Diplomado.
- El template existente seguira resolviendo la unica certificacion de cada modulo; el nuevo modo del template resolvera ademas la ponderacion global entre modulos.

## Entendimiento de la formula

Para una libreta con nota presencial `P` y `N` modulos no presenciales con notas finales `M1 ... Mn`:

```text
nota_final = (P * 0.50) + ((M1 + ... + Mn) / N * 0.50)
```

Esto equivale a que cada modulo no presencial tenga un peso de `50 / N` por ciento. En el ejemplo de Neuroeducacion con siete modulos, cada modulo aporta exactamente `7.142857...%`. La interfaz o documentacion puede mostrar `7.14%`, pero el calculo no redondeara cada peso antes de sumar para evitar que el bloque quede en `49.98%`.

## Hallazgos del repositorio

- Ya existe el addon custom `addons-extra/extrairg/irg_diploma_gradebook_weighting` y contiene una primera implementacion de la formula 50/50.
- El core custom `isep_gradebook` calcula actualmente `total_final` como promedio simple de los subjects obligatorios.
- `app.gradebook` y `app.gradebook.template.line` ponderan tipos de evaluacion dentro de un subject (examen, asignacion, interaccion y foro); no permiten asignar pesos diferentes entre subjects.
- La extension debe seguir realizandose en el addon custom y no modificar `isep_gradebook`.
- La deteccion actual del subject presencial solo acepta el nombre exacto `Modulo Presencial`. No reconoce el formato real indicado: `<nombre del diplomado> - MODULO PRESENCIAL`.
- Existen cambios locales sin commit relacionados con recuperacion de diplomados. Se preservaran y el cambio de ponderacion se integrara de forma acotada sin sobrescribirlos.

### Evidencia de la replica de produccion (solo lectura)

- Libreta analizada: `app.gradebook.student(719)`; la transaccion PostgreSQL fue verificada con `transaction_read_only=on`.
- Curso: `Diplomado en Evaluacion e Intervencion desde las Terapias de Tercera Generacion`.
- La categoria del producto es `Diplomado`, codigo `D`; `course_type_id` esta vacio, por lo que no es una fuente suficiente para identificar diplomados.
- Template actual de la libreta: `Solo Examen`, con una linea `exam`, peso `100%`, cantidad `1`.
- El template `Solo Examen` esta compartido: 12 libretas lo usan, 11 de Master y solo una de Diplomado. No debe alterarse globalmente.
- La libreta contiene seis modulos ordinarios con nota `10` y un modulo presencial con nota `8.44`.
- El nombre real del presencial termina en `MÓDULO PRESENCIAL/HOMECLASS`.
- La media simple actual almacenada es `9.78`; la formula 50/50 esperada produce `9.22`.
- Existe `irg_gradebook_editable_template`, que permite seleccionar manualmente `gradebook_id` en la libreta mientras no esta finalizada.

## Inspeccion de base espejo

- El usuario autoriza consultar una base PostgreSQL espejo para analizar la libreta real indicada, sin modificar datos.
- Las credenciales se cargaran desde un `.env` local ignorado por Git y nunca se copiaran a `plan.md`, `execution.log`, `verification.json`, artefactos, comandos mostrados ni documentacion.
- La conexion debe utilizar un usuario PostgreSQL de solo lectura y SSL cuando el servidor lo soporte o exija.
- Las consultas se limitaran a `SELECT` y metadatos necesarios para identificar la libreta, su template, subjects y resultados.
- La creacion del `.env` y el acceso quedan sujetos al veredicto previo del Security Advisor.

## Regla de identificacion propuesta

1. Confirmar que la libreta pertenece a un Diplomado usando, por orden, categoria de producto (`D`/`DI*` o nombre Diplomado), tipo de curso cuando exista y nombre del curso como fallback conservador.
2. Normalizar mayusculas, acentos y espacios.
3. Reconocer como presencial el subject que:
   - sea exactamente `Modulo Presencial`; o
   - termine en el sufijo ` - Modulo Presencial`, como `Diplomado en Neuroeducacion - MODULO PRESENCIAL`; o
   - termine en ` - Modulo Presencial/Homeclass`, variante comprobada en produccion.
4. Considerar solo subjects obligatorios para el bloque ordinario, conservando la regla actual del gradebook.
5. Exigir un unico subject presencial identificable. Los casos con ninguno o con mas de uno no deben producir un calculo 50/50 ambiguo; se conservara el calculo estandar y se registrara el caso para diagnostico.

## Alcance tecnico previsto

### Implementacion

- Crear un addon nuevo `irg_diploma_gradebook_template_weighting` para no modificar addons existentes, dependiendo de `irg_diploma_gradebook_weighting` e `irg_gradebook_editable_template`.
- Extender `app.gradebook` con un modo de calculo final (`standard` / `diploma_50_50`).
- Crear un template seleccionable nuevo, `Diplomado - Solo examen - Ponderacion 50/50`, con una certificacion/examen al 100% dentro de cada modulo y modo final `diploma_50_50`.
- Mantener intacto el template compartido `Solo Examen`.
- Aplicar la formula especial solo si coinciden las dos condiciones: template en modo `diploma_50_50` y curso identificado como Diplomado.
- Ajustar el helper de deteccion del subject presencial.
- Mantener una unica funcion pura/concentrada que devuelva:
  - nota presencial;
  - promedio del bloque no presencial;
  - cantidad y peso matematico de los modulos ordinarios;
  - nota final 50/50.
- Aplicar el resultado tanto a `total_final` como a `avg_score`, despues de llamar a `super()`.
- No almacenar pesos redondeados por modulo ni modificar manualmente todas las plantillas de cada diplomado.
- Usar `final_subject_note` como nota del examen de certificacion: el usuario confirmo que es la unica evaluacion tanto del subject presencial como de cada subject no presencial.
- Mantener intacta la logica local de recuperacion salvo los ajustes de dependencias de computo que resulten necesarios.

### Pruebas TDD

Antes del ajuste se incorporaran pruebas que fallen con el comportamiento actual y cubran:

1. Subject `Diplomado en Neuroeducacion - MODULO PRESENCIAL` reconocido pese a mayusculas y acentos.
2. Siete modulos ordinarios: el bloque suma exactamente 50% sin usar `7.14 * 7`.
3. Formula numerica con notas distintas para comprobar que no se usa promedio simple.
4. Numero variable de modulos (por ejemplo 3, 6 y 7), siempre repartiendo `50 / N`.
5. Curso no Diplomado: conserva el promedio estandar.
6. Diplomado sin modulo presencial: conserva el comportamiento estandar.
7. Diplomado con dos candidatos presenciales: no elige arbitrariamente el primero.
8. Exclusión de subjects no obligatorios del bloque del 50%.
9. Recalculo al cambiar una nota, el nombre del subject o el tipo de curso.
10. Convivencia con la recuperacion de diplomado ya presente en los cambios locales.
11. Template `Solo Examen` existente conserva el calculo estandar incluso en cursos no Diplomado.
12. Nuevo template 50/50 seleccionado en un Master conserva el calculo estandar por la salvaguarda de tipo/categoria.
13. Caso de regresion basado en la libreta 719: seis notas 10 y presencial 8.44 producen 9.22.

### Validacion

- Ejecutar los tests del modulo en el entorno obligatorio `docker-compose.local.yml`.
- Ejecutar validaciones de instalacion/actualizacion del addon en Odoo 16.
- Comprobar sintaxis Python, parseo XML y lint/format aplicable.
- Guardar las salidas en `missions/diploma-specific-grade-weighting/artifacts/`.
- Emitir `verification.json`; la mision solo podra cerrarse con `status: passed` y todos los checks relevantes aprobados.
- Si falla la validacion, aplicar el escalado reactivo `standard -> complex` y registrar el reintento en `execution.log`.

### Documentacion

- Actualizar la micro-spec y la documentacion del addon con la regla del sufijo real.
- Documentar la formula exacta y aclarar que `7.14%` es solo una representacion visual de `50/7`.
- Añadir changelog y persistir el patron reutilizable en `.agents/knowledge/`.
- Generar `diff.patch` y completar `execution.log`.

## Archivos previstos

- `addons-extra/extrairg/irg_diploma_gradebook_template_weighting/__init__.py`
- `addons-extra/extrairg/irg_diploma_gradebook_template_weighting/__manifest__.py`
- `addons-extra/extrairg/irg_diploma_gradebook_template_weighting/models/__init__.py`
- `addons-extra/extrairg/irg_diploma_gradebook_template_weighting/models/app_gradebook.py`
- `addons-extra/extrairg/irg_diploma_gradebook_template_weighting/models/app_gradebook_student.py`
- `addons-extra/extrairg/irg_diploma_gradebook_template_weighting/views/app_gradebook_views.xml`
- `addons-extra/extrairg/irg_diploma_gradebook_template_weighting/data/gradebook_template_data.xml`
- `addons-extra/extrairg/irg_diploma_gradebook_template_weighting/tests/__init__.py`
- `addons-extra/extrairg/irg_diploma_gradebook_template_weighting/tests/test_diploma_template_weighting.py`
- `doc/micro-specs/2026-06-18-irg_diploma_gradebook_weighting.md`
- `doc/modules/extrairg/irg_diploma_gradebook_weighting.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diploma_gradebook_weighting.md` (nuevo, si no existe al documentar)
- `missions/diploma-specific-grade-weighting/*`

El alcance podra ampliarse solo si la inspeccion TDD demuestra que la unica certificacion no llega de forma inequivoca a `final_subject_note`.

## Complejidad y routing

Tier inicial actualizado: `complex`.

Justificacion objetiva: el diseño confirmado supera cinco archivos, crea un addon y template nuevos, cruza `app.gradebook`, `app.gradebook.student`, curso/producto/categoria, datos XML, vistas y pruebas. No afecta autenticacion, concurrencia, migraciones destructivas ni borrado de datos. El acceso a la replica y el `.env` ya fueron revisados y aprobados por el Security Advisor.

- Plan: agente principal/orquestador con modelo de razonamiento alto.
- Implementacion: subagente codificador con modelo intermedio fuerte, solo despues del OK del usuario.
- Validacion: subagente testeador independiente con modelo intermedio; escalara si aparecen fallos complejos.
- Documentacion: subagente documentador ligero, solo despues de `verification.json` pasado.

## Fuera de alcance

- Modificar directamente `isep_gradebook` u otros addons existentes.
- Configurar a mano porcentajes distintos para cada diplomado.
- Cambiar la regla de recuperacion general, salvo preservar su compatibilidad.
- Hacer commit o push. Cualquier push a `Dev_iRG` requerira un OK explicito nuevo.

## Puerta de revision

Plan aprobado por el usuario el 2026-07-15. Se autoriza iniciar Implementacion. El examen de certificacion es la unica evaluacion de todos los subjects afectados.
