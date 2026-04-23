# Patrones SCSS para Odoo 16

## Cómo funciona el sistema de assets en Odoo 16

Odoo 16 compila SCSS en el servidor usando LibSass. El orden de compilación es:
1. Variables Bootstrap (definidas por Odoo en `web/static/src/scss/bootstrap_overrides.scss`)
2. Bootstrap source
3. Estilos de Odoo
4. Assets de los módulos instalados (en orden del manifest)

**Para sobreescribir variables Bootstrap, el SCSS debe cargarse con `prepend`:**
```python
# __manifest__.py
'assets': {
    'web.assets_frontend': [
        ('prepend', 'mi_modulo/static/src/scss/mi_variables.scss'),
    ],
},
```

## Variables Bootstrap disponibles en Odoo 16

Odoo expone todas las variables Bootstrap 5 más algunas propias:

### Colores
```scss
$primary        // Color primario (botones, links activos)
$secondary      // Color secundario
$success        // Verde
$danger         // Rojo
$warning        // Amarillo/naranja
$info           // Azul info
$light          // Fondo claro
$dark           // Fondo oscuro
$white          // Blanco
$black          // Negro

// Grises (Bootstrap 5)
$gray-100 .. $gray-900

// Colores semánticos Odoo
$o-main-color-1   // Usado en navbar
$o-main-color-2   // Usado en acentos
```

### Tipografía
```scss
$font-family-base        // Familia base del cuerpo
$font-family-sans-serif  // Sans-serif fallback
$font-size-base          // 1rem por defecto
$font-weight-normal      // 400
$font-weight-bold        // 700
$line-height-base        // 1.5
$headings-font-family    // Fuente de títulos (puede ser diferente a base)
$headings-font-weight    // Peso de headings
$h1-font-size .. $h6-font-size
```

### Espaciado y layout
```scss
$spacer          // 1rem (base del sistema de espaciado)
$border-radius   // Redondeo de bordes estándar
$border-radius-lg
$border-radius-sm
$border-color    // Color de bordes
$box-shadow      // Sombra estándar
$box-shadow-sm
$box-shadow-lg
```

### Navbar (Bootstrap 5)
```scss
$navbar-padding-y
$navbar-padding-x
$navbar-dark-color
$navbar-dark-hover-color
$navbar-light-color
$navbar-light-hover-color
$navbar-light-active-color
$navbar-toggler-border-radius
```

## Patrón correcto para `_variables.scss`

```scss
// ============================================================
// IRG Theme — Bootstrap & Odoo Variable Overrides
// IMPORTANTE: Este archivo se carga con 'prepend' en el manifest
// para que las variables estén disponibles cuando Bootstrap compila.
// ============================================================

// --- Paleta corporativa ---
$primary:             #061d32;
$secondary:           #ca5400;
$body-bg:             #f8f9fa;
$body-color:          #212529;

// --- Tipografía ---
$font-family-base:    'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
$headings-font-family: $font-family-base;
$headings-font-weight: 700;

// --- Bordes y redondeos ---
$border-radius:       0.75rem;
$border-radius-lg:    1rem;
$border-radius-sm:    0.5rem;
$border-color:        rgba(0, 0, 0, 0.1);

// --- Sombras ---
$box-shadow-sm:       0 2px 8px rgba(0, 0, 0, 0.08);
$box-shadow:          0 4px 16px rgba(0, 0, 0, 0.12);
$box-shadow-lg:       0 8px 32px rgba(0, 0, 0, 0.16);

// --- Botones ---
$btn-border-radius:         999px;   // Botones píldora
$btn-border-radius-lg:      999px;
$btn-border-radius-sm:      999px;
$btn-font-weight:           600;
$btn-padding-x:             1.5rem;
$btn-padding-x-lg:          2rem;
```

## Selectores Odoo 16 más usados en frontend

### Navbar
```scss
.o_main_nav              // Contenedor principal de la navbar
.o_website_navbar        // Navbar del website builder
nav#top                  // ID de la navbar en website
.o_nav_logo              // Logo en navbar
```

### Contenido principal
```scss
#wrapwrap            // Wrapper raíz de todas las páginas
#wrap                // Contenido principal (bajo la navbar)
.o_website_main      // Contenido principal alternativo
.o_portal_wrap       // Wrapper del portal
```

### Footer
```scss
footer, #footer      // Footer general
.o_footer            // Footer del website builder
```

### eLearning (website_slides)
```scss
.o_wslides_course_main         // Página de curso
.o_wslides_course_header       // Cabecera del curso
.o_wslides_slides_list         // Lista de lecciones
.o_wslides_slide_link          // Enlace a lección
.o_wslides_lesson_content_type // Tipo de contenido
```

### Shop/eCommerce
```scss
.o_wsale_products_main_col  // Grid de productos
.oe_product_cart            // Tarjeta de producto
.oe_product_image           // Imagen de producto
.oe_product_price           // Precio del producto
.o_cart_summary             // Resumen del carrito
```

### Portal
```scss
.o_portal_wrap          // Layout del portal
.portal-body            // Cuerpo del portal
.o_portal_sidebar       // Sidebar del portal
.o_documents_portal     // Documentos en portal
```

## Anti-patrones a evitar

```scss
// MAL: Colores hardcoded — difícil de mantener y no respeta el tema
.mi-clase {
    background: #061d32;
    color: #ca5400;
}

// BIEN: Usar variables Bootstrap — respeta el sistema de diseño
.mi-clase {
    background: $primary;
    color: $secondary;
}

// MAL: Importar fuentes en SCSS (causa problemas con LibSass de Odoo)
@import url('https://fonts.googleapis.com/...');

// BIEN: Importar fuentes vía layout_overrides.xml en el <head>
// <link rel="preconnect" href="https://fonts.googleapis.com"/>
```

## Compatibilidad con módulos existentes

Los siguientes módulos del proyecto ya usan variables Bootstrap y se beneficiarán
automáticamente al sobreescribir `$primary` / `$secondary` con `prepend`:
- `irg_elearning_styles_rework` — usa `$primary`, `$info`, `$border-color`, `$black`, `$white`
- `irg_timetable_portal_modern_ui` — usa variables Bootstrap en SCSS
