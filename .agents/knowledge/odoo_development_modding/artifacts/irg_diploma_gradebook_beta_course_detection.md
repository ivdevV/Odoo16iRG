# Detección robusta de Diplomados con clasificación inconsistente

## Contexto

En una base beta, una libreta podía mostrar un curso cuyo nombre era claramente
`Diplomado ...`, mientras su `course_type_id` o la categoría de su producto
seguían identificándolo como formación continua. La plantilla 50/50 se guardaba
correctamente, pero `_is_diplomado_course()` devolvía falso y el cálculo caía a
la media estándar: `9,78` en vez de `9,22`.

## Diagnóstico reutilizable

Cuando un campo calculado no cambia después de guardar varias veces el selector
que figura en sus dependencias, no asumir primero un problema de recomputación.
Verificar cada guard clause del helper funcional con los datos reales de esa
base. Un fallback silencioso puede producir un resultado válido, pero
funcionalmente incorrecto, y ocultar la condición que falló.

En este caso, el chatter confirmó que `gradebook_id` sí cambiaba. La prueba que
reprodujo categoría/tipo inconsistentes y un nombre de Diplomado reprodujo
exactamente la media estándar observada.

## Patrón aplicado

Crear un addon puente posterior que extienda solo el criterio de detección:

1. llamar primero a `super()` para preservar fuentes estructuradas válidas;
2. usar una señal secundaria únicamente cuando el criterio heredado falla;
3. normalizar el texto con el helper existente;
4. aceptar solo un patrón inequívoco y acotado; y
5. mantener una barrera funcional independiente, en este caso la selección
   explícita del modo `diploma_50_50`.

El patrón de nombre aceptado es `Diplomado`/`Diplomados` al inicio o después de
` - `. Esto cubre `Diplomado en ...` y `TG - Diplomado en ...`, sin convertir
un curso normal en Diplomado por una mención incidental.

## Pruebas mínimas de regresión

- Clasificación estructurada no-Diplomado + nombre inequívoco + template
  especial: seis notas `10` y presencial `8,44` producen `9,22`.
- El mismo caso comienza en template estándar con `9,78` y cambia a `9,22` al
  seleccionar el especial, demostrando que el compute sí se invalida.
- Curso sin identificador de Diplomado + template especial conserva `9,78`.

## Resultado validado

`irg_diploma_gradebook_beta_course_detection` pasó tres pruebas Odoo en una
base aislada con `docker-compose.local.yml`: 0 fallos y 0 errores. No modifica
la clasificación almacenada ni ejecuta migraciones o recálculos masivos.
