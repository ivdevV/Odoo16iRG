# Misión: Corrección definitiva de tamaño del video embebido en sección destacada

## Alcance y Objetivos
1. Resolver el problema de que el video embebido siga viéndose pequeño. Hemos identificado un colapso en el contenedor flex (`d-flex`) al no tener definida la propiedad `flex-grow-1` en el contenedor del contenido, lo cual genera una dependencia circular de ancho con el iframe hijo.
2. Añadir un bloque `<style>` directo en la plantilla XML de Odoo para evitar fallos de caché de activos CSS frontend en producción/staging.

## Clasificación de Complejidad
- **Clasificación:** `trivial`
- **Justificación:** Afecta a 1 solo archivo de vista XML (`website_slides_templates.xml`). No introduce lógica en base de datos ni afecta a controladores ni seguridad.

## Modelos Elegidos para cada Fase
- **Plan:** Orquestador (Gemini 3.5 Flash)
- **Implementación:** Codificador (Gemini 3.5 Flash)
- **Validación:** Testeador (Gemini 3.5 Flash)
- **Documentación:** Documentador (Gemini 3.5 Flash)

## Tareas Propuestas
1. Modificar `website_slides_templates.xml` para añadir la clase `flex-grow-1` a la etiqueta `div` con clase `o_irg_featured_section_content`.
2. Añadir un bloque `<style>` inline dentro de la sección destacada para garantizar la aplicación inmediata de las reglas CSS de escalado del iframe (16:9 y max-width 800px) sin depender de recompilaciones de bundles.
