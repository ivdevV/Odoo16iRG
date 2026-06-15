# irg_elearning_url_slide

## Contexto

Para anadir nuevas categorias de contenido a `website_slides` en Odoo 16 no basta con extender `slide.slide.slide_category` y `slide.slide.slide_type`.

## Gotcha

`website_slides` calcula estadisticas usando campos con patron `nbr_<slide_category>`. Si se anade una categoria `url`, deben existir tanto `slide.channel.nbr_url` como `slide.slide.nbr_url`; de lo contrario aparece `KeyError: 'nbr_url'` durante recomputos de `_compute_slides_statistics`.

## Patron Aplicado

- Anadir `selection_add` en `slide.slide.slide_category`.
- Anadir `selection_add` en `slide.slide.slide_type` y ajustar `_compute_slide_type`.
- Anadir contador `slide.channel.nbr_<categoria>`.
- Anadir contador `slide.slide.nbr_<categoria>`.
- Si se requiere fullscreen, anadir `slide.embed_code` y extender el player JS/XML de `website_slides`.

## Validacion

La mision `irg_elearning_url_slide` valido instalacion y tests enfocados en base limpia `validation_url_slide_20260615_c` con `docker-compose.local.yml`.
