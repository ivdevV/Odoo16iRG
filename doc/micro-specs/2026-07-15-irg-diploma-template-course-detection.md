# Micro-spec: deteccion de Diplomado para ponderacion 50/50

## Problema

Una libreta beta de un curso cuyo nombre comienza por `Diplomado` mantiene la
media simple 9,78 al seleccionar la plantilla 50/50. La deteccion existente
descarta el curso si tiene una categoria de producto configurada que no esta
clasificada como Diplomado.

## Cambio propuesto

Crear un addon puente que extienda la deteccion existente y considere tambien
la etiqueta inequivoca del nombre del curso. La ponderacion solo se aplicara si
el template seleccionado usa `final_calculation_mode = diploma_50_50`.

## Criterios de aceptacion

1. Seis modulos con 10 y un modulo presencial con 8,44 producen 9,22.
2. El cambio de template estandar al template 50/50 recalcula el promedio.
3. Templates normales y cursos sin identificacion de Diplomado no cambian.
4. La compatibilidad con la exclusion NLEX se conserva por dependencia.

## Riesgos y limites

El nombre del curso pasa a ser una fuente valida de clasificacion solo cuando
contiene una etiqueta explicita de Diplomado. No se modifican datos existentes
ni se ejecutan migraciones.
