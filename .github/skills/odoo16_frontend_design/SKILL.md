---
name: odoo16_frontend_design
description: >
  Especialista en diseño frontend para sitios web Odoo 16 self-hosted.
  Usa cuando quieras diseñar, rediseñar, modificar o revisar la apariencia visual
  del website de Odoo 16: temas, SCSS, variables Bootstrap, plantillas QWeb, navbar,
  footer, portal del alumno, eLearning, tienda, checkout, componentes UI.
  Crea módulos irg_website_* con _inherit, xpath, prepend en assets_frontend.
  Combina conocimiento de patrones SCSS de Odoo 16 con principios UI/UX profesionales.
  Keywords: theme, diseño web, frontend, CSS, SCSS, Bootstrap variables, QWeb layout,
  website.layout, irg_website_theme, rediseño, navbar, portal, campus, eLearning, shop.
---

# Skill: Frontend Design para Odoo 16 (self-hosted)

## Propósito
Guiar el diseño e implementación de personalizaciones visuales para el sitio web de
una instancia Odoo 16 self-hosted, siguiendo la arquitectura de herencia del proyecto
(nunca modificar módulos existentes) y los estándares de calidad UI/UX.

## Restricciones irrenunciables (heredadas del proyecto)
- **NUNCA** editar módulos existentes (`isep_website_custom`, `website`, ni ningún nativo).
- Toda personalización en un módulo `irg_*` nuevo usando `_inherit` / `xpath`.
- Los módulos van en `addons-extra/extrairg/` con prefijo `irg_`.
- Los SCSS deben usar variables Bootstrap de Odoo (`$primary`, `$secondary`, etc.) en lugar de colores hardcoded.
- Inyectar hojas de estilo con `prepend` en `web.assets_frontend` para que las variables se compilen antes que Bootstrap.
- XPath estables: usar `//field[@name='...']` o `//div[@id='...']`, nunca posicionales.

## Cuándo usar esta skill
- Crear o modificar temas visuales para el website de Odoo 16
- Definir paletas de colores, tipografía y espaciado corporativos
- Heredar y sobreescribir plantillas QWeb de website, portal, eLearning, shop
- Diseñar snippets (bloques arrastables) personalizados
- Revisar SCSS existente y refactorizarlo a variables Bootstrap
- Planificar un rediseño completo del sitio

## Procedimiento general

### 1. Análisis de estado actual
- Leer los manifests de `isep_website_custom` y `isep_website_custom_design`
- Identificar colores hardcoded y variables Bootstrap ya usadas
- Revisar qué módulos `irg_*` ya inyectan estilos

### 2. Definir el sistema de diseño
Consultar [referencias de patrones SCSS](./references/odoo16-scss-patterns.md) y
[referencias de QWeb layout](./references/odoo16-qweb-layout.md).
- Paleta: 2 colores primarios + 2 secundarios + 2 neutros
- Tipografía: familia base + tamaños (h1-h6, body, small)
- Espaciado: basado en múltiplos de 4px / 8px
- Componentes: navbar, cards, buttons, badges, breadcrumbs, tablas

### 3. Crear el módulo de tema
Usar la [plantilla de variables](./assets/theme-variables-template.scss) como base.
- `__manifest__.py` con `prepend` obligatorio en `web.assets_frontend`
- `_variables.scss` → override de variables Bootstrap ANTES de importar Bootstrap
- `_typography.scss` → `@import` de Google Fonts + `$font-family-base`
- `_components.scss` → sobrescribir selectores `.o_*` de Odoo con variables
- `views/layout_overrides.xml` → heredar `website.layout` para head/meta/fonts

### 4. Compatibilidad y verificación
- Confirmar que `$primary` y `$secondary` se propagan a módulos dependientes
- Verificar en el contenedor Docker: `docker exec odoo_latest odoo -u irg_website_theme ...`
- Revisar que `irg_elearning_styles_rework` sigue funcionando (usa `$primary`)

## Conocimiento complementario
Esta skill se complementa con:
- `ui-ux-pro-max` (personal) → paletas, tipografías, patrones UI profesionales
- `odoo16_developer` (proyecto) → reglas generales de desarrollo Odoo 16

## Patrones clave de Odoo 16

### Jerarquía SCSS en assets_frontend
```
Bootstrap variables (Odoo defaults)
  ↑ PREPEND: irg_website_theme/_variables.scss  ← sobreescribir aquí
Bootstrap source
Odoo SCSS
isep_website_custom/style.scss
irg_elearning_styles_rework.scss
```

### Manifest mínimo para un tema
```python
'assets': {
    'web.assets_frontend': [
        # prepend = se compila ANTES de Bootstrap
        ('prepend', 'irg_website_theme/static/src/scss/irg_theme.scss'),
    ],
},
```

### Plantillas QWeb clave
| Template | Uso |
|---|---|
| `website.layout` | Layout raíz de todas las páginas web |
| `website.layout_head_default` | `<head>` — añadir fuentes, meta |
| `website.navbar` | Barra de navegación |
| `website.footer` | Pie de página |
| `portal.portal_layout` | Layout del portal del alumno |
| `website_slides.slide_channel_main` | Página de curso eLearning |

## Glosario de selectores Odoo frecuentes
```
.o_website_navbar     → navbar principal
.o_main_nav           → menú de navegación
.o_footer             → footer
.o_portal_wrap        → wrapper del portal
.o_wslides_course_*   → componentes eLearning
.o_wsale_*            → componentes tienda
```
