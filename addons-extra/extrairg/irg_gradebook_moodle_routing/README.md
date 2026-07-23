iRG Gradebook Moodle Routing
============================

Este addon puente añade un enrutamiento explícito de Moodle a la
sincronización de la libreta. Depende de ``irg_gradebook_moodle_wizard``;
instálelo siempre después de su addon base.

Arquitectura
------------

El routing tiene tres niveles::

    Curso Odoo (op.course)
      -> mapa de curso Moodle (ID, nombre, modalidad y edición)
      -> asignatura Odoo (op.subject) y sus Activity IDs Moodle

El mapa de curso guarda el ID y el nombre de Moodle. Solo un nombre con
exactamente un marcador ``(ONLINE)`` o ``(ONLINE AAAA)``, sin distinguir
mayúsculas y minúsculas, se clasifica como Online. En el segundo formato,
``AAAA`` debe contener cuatro dígitos y se guarda como edición. Un nombre no
vacío sin marcador ``(ONLINE`` se clasifica como HomeClass.

Cualquier marcador Online malformado, repetido o no consumido, por ejemplo
``(ONLINE2026)``, ``(ONLINE 26)`` o ``(ONLINE 2026 EXTRA)``, queda sin
modalidad y no es seleccionable. Cada mapa de asignatura se vincula a su mapa
de curso padre y debe usar el mismo Moodle Course ID; además, la asignatura
debe pertenecer al curso Odoo del padre.

Los mapas históricos sin padre se conservan para no perder datos, pero este
routing no los utiliza.

Instalación y actualización
---------------------------

1. Asegure que ``irg_gradebook_moodle_wizard`` está instalado.
2. Añada ``irg_gradebook_moodle_routing`` a la ruta de addons y actualice la
   lista de aplicaciones.
3. Instale el módulo, o actualícelo tras desplegar una versión nueva::

       odoo -c /etc/odoo/odoo.conf -d <base_de_datos> -u irg_gradebook_moodle_routing --stop-after-init

La instalación o el upgrade no migran, borran, desactivan ni reasignan mapas
históricos. Ejecute el importador descrito más abajo para crear o vincular los
mapas autorizados.

Configuración en la interfaz
----------------------------

En el menú raíz de Libreta, abra Cursos Moodle y cree un registro por pareja
curso Odoo / curso Moodle con estos valores:

* Curso Odoo.
* Moodle Course ID positivo.
* Nombre del curso Moodle.
* Estado activo.

La modalidad y la edición son de solo lectura porque se derivan del nombre.
Después, en el listado o formulario de mapas de asignatura Moodle, asigne el
Mapa de curso padre y sus Activity IDs. El servidor rechaza una asignatura
vinculada a un padre de otro curso Odoo o con un Moodle Course ID distinto.

Los usuarios internos pueden leer los mapas de curso. Solo los
administradores de sistema pueden crearlos, modificarlos o borrarlos. Los
permisos de la sincronización y de las notas siguen siendo los del addon base;
la visibilidad de un menú no sustituye la autorización server-side.

Selección por lote y edición
----------------------------

Al cargar datos Moodle desde una libreta, el código del lote decide la ruta:

* Un código que contiene ``HC`` y no ``ONL`` exige exactamente un mapa
  HomeClass activo del curso Odoo.
* Un código que contiene ``ONL`` y no ``HC`` exige un mapa Online activo del
  curso Odoo.

Para un lote Online, se usa primero el mapa cuya edición coincide con el año
de inicio del lote, por ejemplo ``(ONLINE 2026)``. Si no existe, se permite un
único mapa ``(ONLINE)`` genérico. Más de un candidato, la ausencia de
candidato, un marcador Online malformado o un código con ambas etiquetas (o
ninguna) bloquean la carga antes de contactar Moodle. Las asignaturas se
consultan únicamente dentro del mapa de curso seleccionado.

Importación de los CSV
----------------------

El importador espera CSV MacRoman con separador ``;`` y tres fuentes:

* ``mapeo cursos homeclass.csv`` autoriza las parejas curso Odoo / curso
  Moodle HomeClass.
* ``mapeo cursos online.csv`` contiene el inventario autorizado de Moodle
  Course IDs Online.
* ``Mapeo asignaturas.csv`` aporta curso, asignatura, Activity IDs y nombres
  Moodle.

Ejecute una copia de seguridad y pruebe primero en una base de pruebas. Desde
un ``odoo shell``, invoque el importador con rutas absolutas controladas por el
administrador::

    from odoo.addons.irg_gradebook_moodle_routing.tools.import_moodle_routing_csv import run_import

    summary = run_import(
        env,
        "/ruta/controlada/mapeo cursos homeclass.csv",
        "/ruta/controlada/mapeo cursos online.csv",
        "/ruta/controlada/Mapeo asignaturas.csv",
    )
    print(summary)
    env.cr.commit()  # Solo tras revisar una ejecución deliberada.

Para ejecutar la prueba sin persistir cambios, sustituya ``commit()`` por
``env.cr.rollback()``. El resumen agrega registros creados, actualizados y
descartados por motivo sin registrar el contenido de las filas. Un marcador
Online malformado se descarta como ``invalid_online_marker`` antes de tocar el
ORM.

Los encabezados obligatorios se validan antes de procesar cada fuente. Todos
los IDs deben ser enteros positivos PostgreSQL. Se descartan filas inválidas,
no autorizadas, sin registros Odoo o con una asignatura fuera de su curso.

Idempotencia y conservación de datos
------------------------------------

La importación hace upsert de los mapas presentes en los CSV autorizados. Al
repetirla, reutiliza los registros existentes y sus Activity IDs; solo añade
Activity IDs nuevos y actualiza un nombre cuando la fuente aporta uno no
vacío. No ejecuta ``unlink``, no limpia las líneas existentes, no desactiva
registros ni elimina mapas históricos.

Una pareja HomeClass ausente del CSV autorizador, por ejemplo Odoo ``1`` /
Moodle ``36`` mientras solo se autoriza ``35``, no obtiene un mapa padre y
queda fuera de este routing.

Errores y limitaciones
----------------------

* Corrija el código del lote si no identifica exactamente una modalidad.
* Use únicamente ``(ONLINE)`` o ``(ONLINE AAAA)`` para nombres Online; corrija
  cualquier variante malformada antes de reintentar.
* Mantenga un único mapa activo por ruta HomeClass y un único candidato Online
  para cada edición o fallback genérico.
* Si los CSV usan otra codificación, separador, encabezados o IDs, el
  importador falla o descarta las filas no válidas; conviértalos antes de
  reintentar.
* La ruta de importación no obtiene credenciales Moodle ni debe recibir rutas
  desde usuarios web.
* La importación solo enlaza registros Odoo existentes; no crea cursos ni
  asignaturas Odoo faltantes.

Pruebas
-------

La última validación funcional actualizó el addon y ejecutó su suite Odoo en
``test_irg_db``: 20 métodos / 22 pruebas y subpruebas, sin fallos ni errores.
Un smoke reversible procesó los tres CSV reales con ``SAVEPOINT`` y
``ROLLBACK``; la base de prueba no contenía los cursos o asignaturas fuente,
por lo que no creó mapas persistentes. Otro smoke confirmó que tres marcadores
Online malformados se descartaron sin crear ni actualizar mapas. También
pasaron compilación Python, manifest, XML, ACL, alcance y comprobaciones de
diff.

La validación final tiene estado ``passed``. El upgrade terminó sin errores ni
warnings de docutils atribuibles al README. El smoke de importación fue
reversible y confirmó el parseo, las autorizaciones, el rollback y la exclusión
de Odoo ``1`` / Moodle ``36``; ``test_irg_db`` no contenía los registros Odoo
fuente, por lo que no creó mapas reales. La evidencia está en
``missions/fix-gradebook-moodle-course-activity-routing/verification.json``.
