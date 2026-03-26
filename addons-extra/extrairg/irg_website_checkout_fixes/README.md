# iRG Website Checkout Fixes

**Versión**: 16.0.1.0.0  
**Autor**: iRG Desarrollo  
**Licencia**: AGPL-3

## Propósito
Arreglar bugs visuales en la página de checkout `/shop/address`:
- Rellenar valores de cuotas remostradas como `{}`
- Cambiar etiqueta de "Nombre de quíén factura" a "Nombre en la Factura" (corrección de typo)
- Mejorar contraste de inputs (fondo blanco en lugar de gris)

## Cambios implementados
### 1. Cuotas dinámicas
- **Archivo**: `views/website_checkout_templates.xml`
- **Cambio**: Heredar template `website_sale.cart_summary` y usar XPath para reemplazar `{}` con vars dinámicas
- **Sintaxis nueva**: `Cuotas restantes (3):` en lugar de `Cuotas restantes ({})`

### 2. Label de factura
- **Archivo**: `views/website_checkout_templates.xml`
- **Cambio**: XPath en template `website_sale.shop_address` reemplaza label
- **De**: "Nombre de quíén factura" → **A**: "Nombre en la Factura"

### 3. CSS de contraste
- **Archivo**: `static/src/css/checkout_fix.css`
- **Cambio**: Inputs con `background: #ffffff`, `color: #222222`
- **Selectores**: `.oe_website_sale .o_checkout input`, `textarea`, `select`

## Dependencias
- `website_sale` (módulo nativo)

## Instalación
```bash
cd /path/to/Odoo16iRG

# Opción 1: Via odoo CLI
odoo -u irg_website_checkout_fixes -d <yourdb>

# Opción 2: Via UI Odoo
# Ir a Aplicaciones → Instalar módulo "iRG Website Checkout Fixes"
```

## Testing
1. Navegar a `/shop/address` con usuario autenticado
2. Verificar:
   - ✅ Cuotas muestran número (ej: "3"), no `{}`
   - ✅ Label dice "Nombre en la Factura" (sin typo)
   - ✅ Inputs tienen fondo blanco y texto oscuro (legible)
3. Completar checkout end-to-end (debe funcionar sin errores)

## Rollback
```bash
# Desinstalar módulo
odoo -u --uninstall-addons=irg_website_checkout_fixes -d <yourdb>

# O via UI: Aplicaciones → iRG Website Checkout Fixes → Desinstalar
```

## Micro-spec
Ver: `doc/micro-specs/2026-03-16-irg_website_checkout_fixes.md`

## Referencias
- Odoo 16 XPath: https://www.odoo.com/documentation/16.0/developer/reference/frontend/javascript_reference.html
- CSS assets: https://www.odoo.com/documentation/16.0/developer/reference/frontend/assets.html
