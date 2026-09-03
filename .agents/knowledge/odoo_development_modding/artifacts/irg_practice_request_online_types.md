# irg_practice_request_online_types

## Contexto

El combo de tipo de práctica del campus no filtraba por modalidad académica. Un `contains('ONL')` crudo choca con Neurologopedia: `MONLHC` y `MONLPRS` contienen `ONL` dentro de `MONL`, y la online real es `MONLONL`.

## Patrón

Detectar online con código de lote, no con el nombre del curso:

1. Vacío → no online.
2. Prefijo `MONLHC` o `MONLPRS` → no online.
3. Si queda `ONL` en el código → online.

No usar `'ONL' in code and 'MONL' not in code` (excluye `MONLONL`).

El create del portal usa `sudo()` pero el uid sigue siendo portal: el gate `has_group('base.group_portal')` funciona. El JS del filtro solo debe **ocultar**, nunca `hidden = false`, porque un script legacy ya resetea visibilidad y restringe la opción id 2.
