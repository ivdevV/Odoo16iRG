# Patrones QWeb y Layout para Odoo 16 Website

## Arquitectura de plantillas del Website

Odoo 16 usa QWeb como motor de plantillas. Las páginas del website se construyen
mediante herencia en cascada:

```
web.layout
  └── website.layout           ← raíz de todas las páginas web
        ├── website.layout_head_default  ← <head>
        ├── website.navbar               ← navbar
        ├── #wrap                        ← contenido de la página
        └── website.footer               ← footer
```

## Cómo heredar plantillas sin modificarlas

```xml
<odoo>
    <template id="mi_override_layout" inherit_id="website.layout" name="IRG Layout Override">
        <!-- XPath para añadir al <head> -->
        <xpath expr="//head" position="inside">
            <link rel="preconnect" href="https://fonts.googleapis.com"/>
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin=""/>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap"
                  rel="stylesheet"/>
        </xpath>
    </template>
</odoo>
```

## Plantillas clave del website de Odoo 16

### `website.layout` — Layout raíz

**Módulo:** `website`
**Archivo:** `website/views/website_templates.xml`

Estructura básica:
```xml
<t t-name="website.layout">
    <t t-call="web.layout">
        <t t-set="head_website">...</t>
        <t t-set="body_classname">...</t>
        <!-- navbar, wrap, footer -->
    </t>
</t>
```

XPaths estables disponibles:
```xml
<!-- Añadir al <head> -->
<xpath expr="//t[@t-call='web.layout']" position="before"/>
<xpath expr="//head" position="inside"/>

<!-- Añadir antes/después del navbar -->
<xpath expr="//header[@id='top']" position="before"/>
<xpath expr="//header[@id='top']" position="after"/>

<!-- Añadir antes/después del contenido principal -->
<xpath expr="//div[@id='wrap']" position="before"/>
<xpath expr="//div[@id='wrapwrap']" position="inside"/>

<!-- Modificar el footer -->
<xpath expr="//footer" position="replace"/>
<xpath expr="//div[@id='footer']" position="inside"/>
```

### `website.navbar` — Barra de navegación

**ID:** `website.navbar`

XPaths estables:
```xml
<!-- Añadir elemento al menú -->
<xpath expr="//ul[hasclass('o_main_nav')]" position="inside">
    <li class="nav-item">...</li>
</xpath>

<!-- Añadir antes del logo -->
<xpath expr="//a[@class='navbar-brand']" position="before">
    ...
</xpath>

<!-- Añadir botones de acción (derecha) -->
<xpath expr="//div[hasclass('o_main_nav_extra')]" position="inside">
    ...
</xpath>
```

### `website.footer` — Footer

```xml
<!-- Reemplazar contenido del footer -->
<template id="footer_override" inherit_id="website.footer" name="IRG Footer">
    <xpath expr="//div[@id='footer']" position="replace">
        <div id="footer" class="o_footer ...">
            <!-- tu footer -->
        </div>
    </xpath>
</template>
```

### `portal.portal_layout` — Portal del alumno

**Módulo:** `portal`
**XPaths disponibles:**
```xml
<!-- Añadir sidebar -->
<xpath expr="//div[@id='o_portal_sidebar']" position="inside"/>

<!-- Añadir antes del breadcrumb -->
<xpath expr="//ol[hasclass('breadcrumb')]" position="before"/>

<!-- Modificar el contenido principal del portal -->
<xpath expr="//div[hasclass('o_portal_docs')]" position="inside"/>
```

### `website_slides.slide_channel_main` — Curso eLearning

```xml
<!-- Añadir información extra en la cabecera del curso -->
<xpath expr="//div[hasclass('o_wslides_course_header')]" position="inside">
    ...
</xpath>

<!-- Modificar el sidebar del curso -->
<xpath expr="//div[hasclass('o_wslides_sidebar')]" position="replace">
    ...
</xpath>
```

## Registrar un override de template en el manifest

```python
# __manifest__.py
'data': [
    'views/layout_overrides.xml',
],
```

> IMPORTANTE: Los templates de website se cargan en el array `data`, no en `views` separado.
> No es necesario incluirlos en `security/` ni en el orden especial, salvo que dependa de datos.

## Snippets personalizados (bloques arrastables)

Para crear un snippet arrastrable en el website builder:

```python
# manifest — registrar la vista del snippet y la opción
'data': [
    'views/snippets/irg_hero_snippet.xml',
    'views/snippets/options/irg_hero_snippet_options.xml',
],
```

```xml
<!-- views/snippets/irg_hero_snippet.xml -->
<odoo>
    <!-- 1. El bloque en sí -->
    <template id="irg_hero" name="IRG Hero Banner">
        <section class="irg_hero_section">
            <!-- contenido del snippet -->
        </section>
    </template>

    <!-- 2. Registrar en la categoría de snippets del builder -->
    <template id="snippets_irg" inherit_id="website.snippets" name="IRG Snippets">
        <xpath expr="//div[@id='snippet_content']" position="inside">
            <t t-snippet="irg_website_theme.irg_hero"
               t-thumbnail="/irg_website_theme/static/src/img/snippets/hero.svg"/>
        </xpath>
    </template>
</odoo>
```

## Páginas especiales del website ISEP/IRG

| URL | Template de Odoo | Módulo |
|---|---|---|
| `/campus` | `isep_website_custom.dashboard_campus` | `isep_website_custom` |
| `/slides` | `website_slides.slide_channel_list_main` | `website_slides` |
| `/slide/<course>` | `website_slides.slide_channel_main` | `website_slides` |
| `/my/home` | `portal.portal_my_home` | `portal` |
| `/shop` | `website_sale.shop` | `website_sale` |
| `/shop/cart` | `website_sale.cart` | `website_sale` |
| `/shop/address` | `website_sale.address` | `website_sale` |
| `/forum` | `website_forum.forum_index` | `website_forum` |

## XPath — Reglas de seguridad

| Tipo | Ejemplo | Estabilidad |
|---|---|---|
| Por atributo `id` | `//div[@id='footer']` | Alta |
| Por clase hasclass | `//div[hasclass('o_wslides_course_header')]` | Alta |
| Por atributo `name` en field | `//field[@name='partner_id']` | Alta |
| Combinados | `//header[@id='top']//a[@class='navbar-brand']` | Alta |
| Por posición | `//div[1]` | Baja — EVITAR |
| Por texto | `//button[text()='Guardar']` | Media — EVITAR |

## Variables Odoo en QWeb

```xml
<!-- Variables siempre disponibles en templates de website -->
<t t-set="website" t-value="website"/>  <!-- el objeto website activo -->
<t t-set="main_object" t-value="..."/> <!-- objeto principal de la página -->
<t t-set="user_id" t-value="..."/>     <!-- usuario actual -->
<t t-set="editable" t-value="..."/>    <!-- si está en modo edición -->
```
