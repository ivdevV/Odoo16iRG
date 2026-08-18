# Categoría Moodle opcional en `slide.channel`

## Contexto

`odoo_moodle_connector` declara `slide.channel.category_id` como obligatorio. Cuando el conector está instalado solo como dependencia y no existe sincronización Moodle, esa obligatoriedad puede bloquear formularios y la acción «Ir a sitio web» aunque el curso sea exclusivamente local.

## Patrón aplicado

- Crear un módulo puente que dependa directamente de `odoo_moodle_connector`.
- Redefinir el mismo `Many2one` mediante `_inherit = 'slide.channel'` con `required=False`.
- Heredar la vista concreta del conector y aplicar `required="0"` al campo para que servidor y cliente expresen el mismo contrato.
- No modificar los métodos de sincronización ni el módulo original.

## Gotcha

Hacer opcional el campo no adapta el servicio remoto. Si posteriormente existen credenciales Moodle, el flujo original seguirá intentando sincronizar y Moodle puede requerir una categoría válida. En ese escenario debe asignarse categoría o diseñarse por separado una política explícita para omitir sincronización en cursos locales.

## Validación recomendada

Comprobar en una base aislada:

1. `category_id.required is False`.
2. La vista efectiva tiene `required="0"`.
3. Un curso puede crearse y editarse con `category_id=False` y sin credenciales Moodle.
