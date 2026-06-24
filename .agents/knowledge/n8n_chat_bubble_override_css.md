# Overriding Odoo styles in Dynamic UI elements (like chat bubbles)

## Contexto
Al inyectar elementos dinámicos en vistas de Odoo (como reproductores de eLearning, layouts o ventanas de chat de terceros, como n8n chat), los estilos CSS globales del framework pueden superponerse de forma imprevista y romper la maquetación.

## Aprendizaje / Buenas Prácticas

1. **Uso de `.style.setProperty()` con `important`**:
   Para forzar estilos inline en elementos creados mediante JavaScript y garantizar que anulen las reglas de estilo de Odoo (que a menudo usan selectores complejos y con `!important`), se debe usar `element.style.setProperty('property', 'value', 'important')`. La asignación directa `element.style.property = 'value'` no admite el flag `!important` y suele ser anulada.

2. **Micro-interacciones responsivas en XML**:
   Para los elementos inyectados que deben ser interactivos:
   - Se debe definir el estado inicial responsivo (por ejemplo, oculto en móviles: `display: none !important`) en las hojas de estilo del XML.
   - Usar transiciones fluidas en cambios de opacidad, background-color y transformaciones (`scale`) en el hover y active para dar una experiencia premium y nativa.

3. **Conmutación dinámica de SVG e Iconos**:
   Al interactuar con elementos que cambian de estado (como expandir/contraer pantalla completa), es mejor modificar los atributos SVG (`d` del path) e innerHTML del contenedor de texto de forma sincronizada en el manejador del evento de clic.
