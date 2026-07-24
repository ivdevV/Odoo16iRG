iRG Gradebook Moodle Iteminstance
=================================

Este addon puente amplía la sincronización de notas para reconocer los tres
identificadores que Moodle expone para una actividad:

* ``id``: identificador del grade item;
* ``cmid``: identificador del módulo del curso;
* ``iteminstance``: identificador de la instancia de la actividad.

Los CSV históricos de iRG contienen ``iteminstance``. Por ejemplo, el valor
``205`` puede corresponder a un grade item con ``id=555``, ``cmid=3290`` e
``iteminstance=205``.

Instalación
-----------

Instale ``irg_gradebook_moodle_iteminstance`` después de
``irg_gradebook_moodle_homeclass_editions``. La dependencia del manifiesto
garantiza el orden. No es necesario volver a importar ni modificar los mapeos
existentes.

Comportamiento
--------------

Cada ID configurado se busca simultáneamente en ``id``, ``cmid`` e
``iteminstance``:

* una coincidencia permite calcular la nota;
* cero coincidencias se informa como actividad no encontrada;
* varias coincidencias se rechazan como resolución ambigua.

Un mismo grade item solo se cuenta una vez aunque el número aparezca en dos de
sus campos. También se mantienen los controles de tipo ``quiz``/``assign`` y
de reutilización del mismo grade item por varias líneas de mapeo.

Cuando existen varias ediciones HomeClass, una actividad ausente permite probar
el siguiente curso. Una colisión, reutilización o incompatibilidad de tipo
bloquea la asignatura y no se oculta buscando otra edición.

Limitaciones
------------

El addon no selecciona actividades por nombre ni convierte IDs durante la
importación. Si un mismo número identifica grade items distintos entre los tres
espacios de IDs, el administrador debe corregir el mapeo porque el sistema no
elige arbitrariamente.

Pruebas
-------

La validación conjunta de routing, importación, ediciones HomeClass y este
puente ejecuta 94 métodos post-install sin fallos ni errores.
