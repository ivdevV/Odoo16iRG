# Micro-Spec: irg_online_clone_access_fix

## Contexto

Al duplicar contenidos HomeClass a Online con `irg_course_convocatorias_v2`, algunas asignaturas quedaban no clicables para alumnos Online y algunos documentos duplicados no conservaban el binario real.

## Alcance

- Crear un modulo nuevo `irg_online_clone_access_fix` en `addons-extra/extrairg/`.
- Usar herencia Odoo, sin modificar modulos existentes.
- Resolver el canal efectivo de una asignatura para alumnos Online usando el canal clonado cuando exista.
- Sincronizar membresias `slide.channel.partner` hacia el canal Online clonado conservando campos academicos.
- Restaurar la copia de campos binarios de documentos en el bootstrap HomeClass -> Online de `irg_course_convocatorias_v2`.

## Fuera De Alcance

- No se cambian controladores base de `website_slides`.
- No se migran datos historicos automaticamente; el modulo corrige nuevas sincronizaciones y proporciona reconciliacion al ejecutar autoinscripcion/cron.
- No se elimina ni reemplaza `irg_course_convocatorias_v2`.

## Validacion

- Validacion de sintaxis Python y parseo XML.
- Tests Odoo locales con `docker-compose.local.yml` y `test_irg_db`.
- Casos cubiertos: canal efectivo Online, membresia en canal clonado, reconciliacion de membresia HomeClass existente y copia de `document_binary_content`.

## Riesgos

- Si otro modulo hereda posteriormente el mismo bloque QWeb del portal con mayor prioridad, podria requerir un ajuste adicional de prioridad o XPath.
- La copia de binarios lee el contenido del campo attachment; en documentos muy grandes aumenta el coste del bootstrap, pero es necesario para no copiar solo metadatos/hash.
