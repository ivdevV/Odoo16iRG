# Validacion web QR de diplomas y diplomados

## Contexto

Los registros de `irg.diplomado.registry` usan `name` como numero de registro, mientras que `irg.diploma.registry` usa `registry_number`.

## Patron Aplicado

- No hardcodear URLs como `https://institutoraimongaja.com` para la verificación QR, ya que esto rompe el flujo de validación en entornos locales, desarrollo/test (`odoobetairg.laramieuniversity.com`) o servidores alternativos de producción (`app.institutoraimongaja.com`).
- En lugar de eso, usar siempre el parámetro de configuración `web.base.url` de Odoo:
  ```python
  base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or 'https://app.institutoraimongaja.com'
  base_url = base_url.rstrip('/')
  qr_url = "{}/verificar/?{}".format(base_url, urlencode(query_params))
  ```
- Heredar `IrgDiplomaVerificationController` en módulos puente para mantener las mismas rutas `/verificar` y `/verificar_api`.
- Delegar primero en `super()._verify_from_registry_or_stamp()` para no romper diplomas normales.
- Si no aparece diploma normal, buscar `irg.diplomado.registry` por `name`.

## Gotchas

- En tests `HttpCase`, no usar `cls.registry` para guardar un registro de negocio: pisa el atributo interno `registry` de Odoo y rompe `setUp()`.
- Aunque la ruta sea publica, los tests HTTP locales pueden necesitar `self.authenticate('admin', 'admin')` para fijar la base de datos en la sesion.
- `action_reprint()` no regenera si ya existe `attachment_id`; los PDFs antiguos no cambian su QR automaticamente y requieren eliminación previa del attachment para forzar la regeneración.

