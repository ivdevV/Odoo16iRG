# IRG eLearning Moodle Category Optional

Este módulo permite guardar cursos de eLearning (`slide.channel`) sin asignar una categoría de Moodle.

## Instalación

1. Desplegar el directorio `irg_elearning_moodle_category_optional` junto con los addons extra.
2. Actualizar la lista de aplicaciones.
3. Instalar **IRG eLearning Moodle Category Optional**.

El módulo depende de `odoo_moodle_connector`, por lo que Odoo cargará primero el campo original y después aplicará el ajuste.

## Comportamiento

- `Course Category` deja de ser obligatorio en el modelo y en el formulario de cursos.
- Los valores existentes no se modifican.
- No se crean ni sincronizan categorías Moodle.
- La lógica de sincronización del conector permanece intacta.

## Consideración sobre Moodle

El objetivo es permitir cursos locales cuando la instancia no usa sincronización Moodle. Si en el futuro se configuran credenciales y se activa la sincronización, debe asignarse una categoría válida antes de sincronizar porque el servicio remoto puede requerirla.

## Pruebas

El módulo incluye pruebas Odoo que comprueban el contrato del campo, la vista efectiva y la creación/edición de cursos sin categoría. Deben ejecutarse en una base aislada con `docker-compose.local.yml`.
