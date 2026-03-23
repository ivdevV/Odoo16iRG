# Micro-spec: Website Checkout Fixes (Cuotas, Label, CSS)

## Título
Fixes en página `/shop/address`: rellenar cuotas vacías, cambiar label y mejorar contraste

## Resumen objetivo
Arreglar 3 bugs visuales en checkout: (1) cuotas muestran `{}` en lugar de números, (2) label "Nombre de quíen factura" debe ser "Nombre en la Factura", (3) campos del formulario ilegibles (gris sobre gris, necesitan fondo blanco).

## Motivo / justificación
- **Cuotas vacías**: Template usa `{}` sin pasar el valor. Usuarios ven "Cuotas restantes ({})" en lugar de número concreto.
- **Label incorrecto**: Typo/inconsistencia; debe ser "Nombre en la Factura" (más claro para usuarios).
- **Contraste fallido**: Inputs con fondo gris (#ccc) y texto gris; es ilegible. Necesita blanco.
- **Por qué no tocar core**: Modulo `website_sale` es nativo; usamos `inherit_id` + `xpath` para override seguro.

## Alcance exacto
- **Modelos**: Ninguno (cambios solo visuales/template)
- **Vistas XML**:
  - `irg_sale_subscription_esp/views/cart_summary.xml` (líneas con `{}`)
  - `isep_website_sale_custom/views/template.xml` (label + CSS)
- **Assets**: CSS inline en template para inputs
- **Reports**: Ninguno

## Diseño técnico
### Estrategia 1: Cuotas
- Template actual: `Cuotas restantes ({})`
- Fix: Usar XPath en vistas heredadas para reemplazar `{}` con expresión XPath: `<t t-esc="term_count - 1"/>`
- Módulo: `isep_website_sale_custom` → create view que hereda y sustituye

### Estrategia 2: Label
- Buscar: `//label[contains(text(), 'Nombre de quíen factura')]`
- Replace con XPath a: `<label>Nombre en la Factura</label>`
- Módulo: `isep_website_sale_custom`

### Estrategia 3: CSS
- Selector: `.oe_website_sale .o_checkout input, textarea, select` (inputs del checkout)
- Style: `background: #ffffff; color: #222222; border: 1px solid #dcdcdc;`
- Ubicación: Stylesheet heredada via `web.assets_frontend` o inline en template

## Dependencias (`depends` en `__manifest__`)
```python
'depends': [
    'website_sale',
    'isep_website_sale_custom',  # o el módulo que contiene el template original
    'irg_sale_subscription_esp',  # si aplica
],
```

## Backwards-compatibility / migración
- ✅ **Compatible**: Solo cambios visuales, sin cambios de BD ni lógica de modelos.
- ✅ **Rollback**: Desinstalar el módulo y limpiar caché del navegador.
- ✅ **Datos**: Cero impacto en datos.

## Casos de prueba / criterios de aceptación
1. ✅ Cargar `/shop/address` en usuario con plan de cuotas
   - [ ] "Cuotas restantes" debe mostrar número (ej: "3"), no `{}`
   - [ ] "Total en X cuotas" debe mostrar número (ej: "Total en 4 cuotas"), no `{}`
2. ✅ Label del formulario
   - [ ] Campo de nombre debe mostrar "Nombre en la Factura" (sin typo)
3. ✅ Contraste
   - [ ] Inputs del checkout deben tener fondo blanco
   - [ ] Texto debe ser legible (oscuro sobre blanco)
4. ✅ Sin romper nada
   - [ ] Checkout funciona end-to-end (completa compra)
   - [ ] No cambian otros formularios

## Rollback plan
```bash
# Desinstalar módulo (o comentar en addons-extra)
cd c:\Users\Sebastian\Odoo16\Odoo16iRG

# En Odoo shell:
odoo -u irg_website_checkout_fixes -d <yourdb> --uninstall-addons=irg_website_checkout_fixes

# O via UI: Aplicaciones -> Desinstalar módulo
```

## Estimación y responsable
- **Estimación**: 1–2 horas (búsqueda de templates + XPath + CSS)
- **Responsable**: Sebastian (DevOps/Developer)
- **Prioridad**: Media (UX improvement)

---

## Implementación checklist
- [ ] Crear módulo `irg_website_checkout_fixes`
- [ ] Heredar vistas con `inherit_id` + `xpath`
- [ ] Añadir CSS para inputs blancos
- [ ] Tests de aceptación (visual)
- [ ] Changelog + PR con micro-spec referenciada
- [ ] Merge a main tras Q&A
