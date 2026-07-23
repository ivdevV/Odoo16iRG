Administración del mapeo Moodle de libretas
============================================

Este addon representa por separado los cursos Moodle y sus actividades::

    curso Odoo
      -> uno o varios cursos Moodle
           -> asignaturas Odoo del curso
                -> uno o varios Activity IDs Moodle

Depende de ``irg_gradebook_moodle_routing`` y conserva su selección por código
de lote (``HC`` u ``ONL``) y por año de la edición Online.

Administración desde Odoo
-------------------------

El listado de cursos Moodle muestra una fila por pareja curso Odoo / Moodle:
curso e ID Odoo, Moodle Course ID y nombre, modalidad, edición Online, número de
asignaturas y estado. El formulario contiene las asignaturas de esa pareja.

El listado de asignaturas muestra el curso Odoo y su ID, el mapa y curso
Moodle, la asignatura Odoo con su ID, nombre y código, el número y resumen de
Activity IDs y el estado. Las actividades se administran como líneas
individuales; la lista mostrada no es una fuente editable de IDs.

Solo un administrador de sistema (``base.group_system``) puede abrir o ejecutar
el wizard **Importar mapeo Moodle**, disponible en el menú raíz de Libretas. El
control se aplica en la ACL, la acción, el menú y los métodos del servidor.

El wizard recibe exactamente:

* ``mapeo cursos.csv``;
* ``Mapeo asignaturas.csv``.

**Validar** solo analiza y resume los ficheros; no crea, actualiza ni borra
mapas. Además del recuento de filas y motivos, muestra una previsualización de
los mapas de curso, mapas de asignatura y actividades que se crearían o
actualizarían con el estado actual de la base. La previsualización consulta los
registros activos e inactivos con las mismas claves de búsqueda que la
aplicación, pero no escribe ni altera metadatos.

**Confirmar importación** vuelve a analizar en el servidor los mismos bytes y
aplica un *upsert* conservador. No confía en el resumen enviado por el cliente:
la previsualización es informativa y puede variar si los mapas cambian entre la
validación y la confirmación. Cambiar un archivo devuelve el wizard a borrador.
Después de aplicar se pueden abrir los mapas de curso y asignatura afectados.

Formato CSV
-----------

Ambos ficheros usan ``;`` y pueden estar codificados como UTF-8 con BOM o
MacRoman. Cada fichero puede ocupar como máximo 10 MiB decodificados. El
lector CSV es estricto: un fichero malformado, por ejemplo con comillas sin
cierre, bloquea todo su análisis; no se intenta importar sus filas parciales.
Los errores de contenido de una fila válida desde el punto de vista CSV sí se
resumen como omisiones y permiten continuar con las demás filas.

``mapeo cursos.csv`` admite las cabeceras legadas:

* ``Moodle Course ID``
* ``Odoo Subject Name`` (nombre del curso Odoo)
* ``Odoo Subject ID`` (ID del curso Odoo)
* ``Nombre del Curso``

También admite los alias canónicos ``Odoo Course Name`` y ``Odoo Course ID``.
Si una fila rellena a la vez un alias legado y otro canónico con valores
distintos, se omite por ambigüedad.

``Mapeo asignaturas.csv`` requiere:

* ``Curso Nombre``
* ``Odoo Course ID``
* ``Moodle Course ID``
* ``Odoo Subject Name``
* ``Odoo Subject ID``
* ``Odoo Subject Code``
* ``Moodle IDs List``
* ``Moodle Names Found``

Una fila sin ``Moodle IDs List`` se omite y no crea un mapa vacío. Esto incluye
Prácticas, TFM o cualquier asignatura que no tenga actividades. Los IDs
repetidos se deduplican conservando su primera aparición. Los nombres de
actividad se alinean por posición usando ``|``.

Las parejas ``(Odoo Course ID, Moodle Course ID)`` deben estar autorizadas por
el CSV de cursos de la misma carga. Las parejas ``(8, 24)`` y ``(8, 47)``, por
ejemplo, se omitirán como ``missing_course_pair`` mientras no estén en ese
fichero.

El resumen puede contabilizar estos motivos técnicos:

* ``blank_row``: fila vacía;
* ``invalid_id``: identificador inválido o fuera de rango;
* ``invalid_online_marker``: marcador Online inválido;
* ``ambiguous_course_alias``: alias de curso contradictorios;
* ``missing_odoo_record``: registro Odoo inexistente;
* ``name_mismatch``: nombre no coincidente;
* ``code_mismatch``: código de asignatura no coincidente;
* ``subject_not_in_course``: la asignatura no pertenece al curso Odoo;
* ``missing_course_pair``: pareja curso Odoo/Moodle ausente;
* ``conflicting_subject_parent``: padre Odoo contradictorio;
* ``no_activity_ids``: fila sin actividades;
* ``duplicate_activity_id``: Activity ID duplicado;
* ``activity_name_count_mismatch``: distinto número de IDs y nombres.

Uso desde ``odoo shell``
------------------------

Las rutas deben ser absolutas y controladas por el administrador. El análisis
es de solo lectura: no crea, actualiza ni borra mapas y no necesita rollback.
El adaptador de shell usa el mismo servicio de análisis y aplicación que el
wizard, por lo que aplica el mismo contrato de dos archivos, parser estricto,
alias de cabeceras, validaciones, previsualización y *upsert*::

    from odoo.addons.irg_gradebook_moodle_mapping_admin.tools import import_mapping

    plan = import_mapping.analyze_paths(
        env,
        "/ruta/controlada/mapeo cursos.csv",
        "/ruta/controlada/Mapeo asignaturas.csv",
    )
    print(plan.summary)

    result = import_mapping.apply_plan(env, plan)
    print(result)
    env.cr.commit()  # opcional: solo tras revisar y decidir persistir

``apply_plan`` no ejecuta ``commit``. La aplicación hace upsert, añade
actividades nuevas y actualiza metadatos no vacíos, pero nunca ejecuta
``unlink``, vacía los One2many ni desactiva mapas históricos. Para ensayar la
aplicación sin persistir, no haga ``commit`` y termine el shell o ejecute
``env.cr.rollback()``.

Actualización y rollback operativo
----------------------------------

Antes de actualizar, haga una copia de seguridad de la base y del filestore.
Actualice la lista de aplicaciones e instale o actualice
``irg_gradebook_moodle_mapping_admin`` con el procedimiento habitual del
entorno. En el runtime local del repositorio, la comprobación equivalente es::

    docker compose -f docker-compose.local.yml run --rm odoo_local \
      odoo -c /etc/odoo/odoo.conf -d test_irg_db \
      -u irg_gradebook_moodle_mapping_admin --stop-after-init --no-http

Si la validación falla, no confirme la carga. Si una aplicación desde shell aún
no se ha confirmado, use ``env.cr.rollback()``. Tras un ``commit``, restaure la
copia de seguridad siguiendo el procedimiento operativo: el importador no
ofrece borrado masivo ni rollback destructivo automático.

Limitación de la comprobación con CSV reales
--------------------------------------------

La comprobación reversible con las dos copias reales de CSV validó la interfaz,
permisos, parser y análisis sin escrituras. En ``test_irg_db`` faltan los cursos
y asignaturas maestros de origen, por lo que el *preview* resultó en cero
operaciones y no demuestra una aplicación real de esos datos. Para validar una
carga real se necesita una base con ese maestro, una copia de seguridad y una
revisión explícita del *preview* antes de confirmar.
