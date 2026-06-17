# Validacion web QR de diplomados

## Contexto

Los registros de `irg.diplomado.registry` usan `name` como numero de registro, mientras que `irg.diploma.registry` usa `registry_number`.

## Patron Aplicado

- Crear modulo puente separado para no modificar directamente `irg_generacion_diplomas` ni `irg_generacion_diplomados`.
- Heredar `IrgDiplomaVerificationController` y mantener las mismas rutas `/verificar` y `/verificar_api`.
- Delegar primero en `super()._verify_from_registry_or_stamp()` para no romper diplomas normales.
- Si no aparece diploma normal, buscar `irg.diplomado.registry` por `name`.
- Construir QR con `web.base.url.rstrip('/') + '/verificar/?' + urlencode(...)`.

## Gotchas

- En tests `HttpCase`, no usar `cls.registry` para guardar un registro de negocio: pisa el atributo interno `registry` de Odoo y rompe `setUp()`.
- Aunque la ruta sea publica, los tests HTTP locales pueden necesitar `self.authenticate('admin', 'admin')` para fijar la base de datos en la sesion.
- `action_reprint()` no regenera si ya existe `attachment_id`; los PDFs antiguos no cambian su QR automaticamente.
