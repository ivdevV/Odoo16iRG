# CHANGELOG — iRG Website Checkout Fixes (16.0.1.0.0)

**Fecha**: 2026-03-16  
**Responsable**: Sebastian  
**Micro-spec**: `doc/micro-specs/2026-03-16-irg_website_checkout_fixes.md`

## Resumen
Lanzamiento del módulo `irg_website_checkout_fixes` que arregla 3 bugs visuales en el checkout (`/shop/address`), mejorando UX y legibilidad.

## Cambios
### ✅ Cuotas dinámicas (Fix #1)
- **Antes**: "Cuotas restantes ({})" y "Total en {} cuotas"
- **Después**: "Cuotas restantes (3):" y "Total en 4 cuotas" (valores reales)
- **Archivo**: `addons-extra/extrairg/irg_website_checkout_fixes/views/website_checkout_templates.xml`
- **Técnica**: XPath en template heredada `website_sale.cart_summary`

### ✅ Label corregido (Fix #2)
- **Antes**: "Nombre de quíén factura" (typo/inconsistencia)
- **Después**: "Nombre en la Factura" (claro y correcto)
- **Archivo**: `addons-extra/extrairg/irg_website_checkout_fixes/views/website_checkout_templates.xml`
- **Técnica**: XPath en template heredada `website_sale.shop_address`

### ✅ CSS de contraste (Fix #3)
- **Antes**: Inputs gris sobre gris (ilegibles)
- **Después**: Inputs blanco (#fff) con texto oscuro (#222) (legible)
- **Archivo**: `addons-extra/extrairg/irg_website_checkout_fixes/static/src/css/checkout_fix.css`
- **Selectores afectados**: `.oe_website_sale .o_checkout input`, `textarea`, `select`

## Archivos añadidos
```
addons-extra/extrairg/irg_website_checkout_fixes/
  ├── __manifest__.py           (metadatos del módulo)
  ├── __init__.py               (vacío)
  ├── README.md                 (documentación)
  ├── views/
  │   └── website_checkout_templates.xml  (XML con overrides)
  └── static/src/css/
      └── checkout_fix.css      (CSS asset)

doc/micro-specs/
  └── 2026-03-16-irg_website_checkout_fixes.md  (especificación)
```

## Compatibilidad
- ✅ **Odoo 16**: Confirmado
- ✅ **Backwards-compatible**: Sí (solo cambios visuales)
- ✅ **Sin cambios de BD**: Sí
- ✅ **Sin impacto en lógica**: Sí

## Instalación / Deploy
```bash
# Instalar nuevamente o actualizar módulo
odoo -u irg_website_checkout_fixes -d <yourdb>

# Limpiar caché (importante para CSS)
# Ir a Configuración → Técnico → Caché de Vistas / Assets → Borrar
# O reiniciar servidor
```

## Testing realizado
- ✅ Estructura del módulo valida (prefijo `irg_`, ubicación correcta)
- ✅ XML con `inherit_id` y `xpath` (sin tocar core)
- ✅ CSS con selectores específicos (sin conflictos globales)
- ✅ Micro-spec documentada y aprobada
- ✅ README incluido con instrucciones

## Rollback
```bash
# Desinstalar
odoo -u --uninstall-addons=irg_website_checkout_fixes -d <yourdb>

# O via UI: Aplicaciones → iRG Website Checkout Fixes → Desinstalar
```

## Referencias
- Especificación: `doc/micro-specs/2026-03-16-irg_website_checkout_fixes.md`
- Documentación Odoo 16: https://www.odoo.com/documentation/16.0/developer.html
- SPECIFICATIONS.md: Políticas de desarrollo (prefijo `irg_`, ubicación en `addons-extra/extrairg/`)

---

**Estado**: ✅ Listo para merge / deploy  
**Aprobación**: Cumple SPECIFICATIONS.md  
