iRG Gradebook Moodle HomeClass Editions
========================================

Este addon amplía por herencia el routing de Moodle de la libreta para
gestionar varias ediciones HomeClass (HC) activas de un mismo curso Odoo. No
modifica el comportamiento de los lotes Online.

Uso
---

En los mapas de curso Moodle, indique la edición HomeClass en el campo
``Edición HomeClass manual`` cuando el nombre del curso no permita deducirla.
Al sincronizar un lote HC con varios mapas activos, el asistente ordena los
candidatos para cada asignatura de este modo:

#. La edición cuyo año inicial coincide con el año de inicio del lote.
#. Un mapa HomeClass genérico, sin edición.
#. Las demás ediciones HomeClass activas, en orden determinista por ID de
   curso Moodle y por ID interno.

Por ejemplo, para un lote que comienza en 2025, el curso Moodle ``35`` de la
edición ``2025-2026`` se consulta antes que el curso ``36`` de
``2024-2025``. Si el curso 35 contiene una nota válida de una asignatura, se
usa solo esa nota. Si no la contiene, el asistente puede consultar el curso
36 como respaldo para esa misma asignatura.

Reglas de integridad
--------------------

El respaldo se permite únicamente cuando un candidato no aporta una actividad,
alumno o nota utilizable. No se combinan, promedian ni reutilizan notas de dos
ediciones: el primer curso válido gana para cada asignatura.

Una colisión real dentro de un curso permanece incompatible y detiene la
búsqueda para la asignatura. Son ejemplos una actividad que coincide con más
de un ``id`` o ``cmid``, varios mapas activos para la misma asignatura, un
grade item reutilizado o un tipo de actividad distinto del mapeado. Esta regla
evita que una configuración ambigua se oculte tomando una nota de otra
edición.

Edición HomeClass
-----------------

El addon propone el año inicial a partir del nombre del curso cuando encuentra
un periodo académico consecutivo con alguno de estos formatos:

* ``2025-2026``
* ``2025_2026``
* ``2025/2026``

El valor manual tiene prioridad sobre el periodo detectado. Úselo también
cuando el CSV consolidado o el nombre importado no incluyan el periodo
académico. Los formatos con años no consecutivos no se aceptan como edición.

Límites
-------

El addon no crea ni borra mapas, asignaturas ni Activity IDs. Los Activity IDs
se resuelven exclusivamente dentro del curso Moodle padre de cada candidato.
Los lotes Online delegan al routing existente, incluida su selección por
edición y su fallback genérico.
