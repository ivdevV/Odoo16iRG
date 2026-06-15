# irg_elearning_url_slide

## Alcance

Crear un modulo nuevo para Odoo 16 que anada un tipo de contenido `URL` a eLearning (`website_slides`) sin modificar modulos existentes.

El nuevo tipo debe aparecer en el desplegable `Tipo de contenido` de `slide.slide`, permitir configurar una URL y renderizarse como un slide normal del curso con un enlace de acceso en la misma ventana.

## Descomposicion

1. Crear micro-spec obligatoria en `doc/micro-specs/`.
2. Crear modulo `addons-extra/extrairg/irg_elearning_url_slide`.
3. Extender `slide.slide` con `slide_category = url`, `slide_type = url`, campos URL y validaciones.
4. Heredar vista de formulario para mostrar campos URL solo para el tipo `URL`.
5. Heredar templates de `website_slides` para render, icono y soporte en sidebar/fullscreen.
6. Anadir asset JS/XML para que el fullscreen reconozca el contenido URL.
7. Validar sintaxis Python/XML y registrar evidencia.
8. Documentar README/changelog y knowledge reutilizable.

## Clasificacion de Complejidad

Tier: `standard`.

Justificacion: afecta a 2-5 areas del modulo nuevo (modelo, vistas backend, QWeb frontend, assets y tests/documentacion), con logica acotada y sin tocar autenticacion, concurrencia, migraciones de datos, secretos, despliegue ni borrado historico.

## Modelos Elegidos

- Orquestador / Plan: modelo de razonamiento alto disponible.
- Implementacion: tier `standard`, modelo intermedio fuerte de codigo.
- Validacion: tier `standard`, verificacion local con evidencia.
- Documentacion: modelo ligero suficiente.

## Dependencias

- `website_slides`
- `website`
- `web`

## Knowledge Consultada

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
- `.agents/workflows/odoo16_codebase_knowledge.md`
- `SPECIFICATIONS.md`

## Riesgos

- El player fullscreen de `website_slides` requiere asset especifico para categorias custom.
- Algunos modulos custom existentes sobrescriben `t-att-data-embed-code`; el nuevo tipo debe anadirse con herencia de baja agresividad y depender de `website_slides` solamente.
- La URL se abrira en la misma ventana segun requisito del usuario; esto puede sacar al alumno del campus si el destino es externo.

## Criterios de Aceptacion

- `URL` aparece como opcion en `Tipo de contenido`.
- Al seleccionar `URL`, se muestra y exige el campo URL.
- Un slide URL se renderiza en la vista de contenido como un enlace/boton de acceso.
- El enlace no usa `target="_blank"`.
- El tipo tiene icono en listados/sidebar.
- Sintaxis Python/XML valida.
