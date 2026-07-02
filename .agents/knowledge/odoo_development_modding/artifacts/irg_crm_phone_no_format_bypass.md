# Bypass de Validación y Formateo de Teléfonos en Odoo 16

## Contexto del Problema
Odoo 16 implementa validación y formateo automático de números de teléfono tanto en frontend (mediante `widget="phone"` usando la librería JS libphonenumber de Google) como en backend (con `phone.validation.mixin` usando la librería de Python `phonenumbers`). 

Esto provoca que al guardar o editar, Odoo introduzca automáticamente espacios (formato internacional) y pueda alterar o eliminar prefijos específicos (como el prefijo transicional "1" de México, `+521...`).

## Solución Técnica

Cuando se requiera desactivar por completo este formateo para mantener el valor original exacto escrito por el usuario (sin espacios ni cambios), se debe seguir este patrón:

### 1. Desactivación en Frontend (Vistas XML)
Cambiar el widget del campo de `phone` a `char` usando `position="attributes"`. Esto evita que la lógica de JS reescriba el valor al enfocar o desenfocar el campo.

```xml
<xpath expr="//field[@name='phone']" position="attributes">
    <attribute name="widget">char</attribute>
</xpath>
<xpath expr="//field[@name='mobile']" position="attributes">
    <attribute name="widget">char</attribute>
</xpath>
```

### 2. Desactivación en Backend (Modelos Python)
Sobrescribir el método `_phone_format` del modelo heredado para que devuelva el valor original directamente sin procesar, y anular los métodos onchange nativos de validación de teléfono y móvil.

```python
class MyModel(models.Model):
    _inherit = 'my.model'

    def _phone_format(self, number, country=None, company=None, force_format='E164'):
        """Devuelve el número tal y como fue introducido, evitando validaciones en backend."""
        return number

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        """Evita la validación onchange del teléfono."""
        pass

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        """Evita la validación onchange del móvil."""
        pass
```
