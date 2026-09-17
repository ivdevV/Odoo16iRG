# XPath QWeb: validar la forma real del padre

## Gotcha

El nombre de una clase no implica el tipo de etiqueta que la contiene. En Odoo 16,
`website_slides.course_slides_list_slide` usa la clase
`o_wslides_slides_list_slide` sobre un `li` con `t-attf-class`. Un XPath que busque
un `div` con esa clase es XML válido, pero la instalación falla porque no localiza
ningún nodo en la vista padre.

## Patrón

- Consulte la versión exacta de la plantilla padre y las herencias ya instaladas.
- Para clases dinámicas en `t-attf-class`, seleccione el tipo real de nodo y use
  `contains(@t-attf-class, 'clase_objetivo')`.
- Aplique condiciones de visibilidad al contenedor completo cuando iconos, badges y
  controles tampoco deban quedar expuestos.
- Añada una prueba que extraiga el XPath del XML del addon y lo confronte con una
  fixture mínima de la estructura oficial, exigiendo exactamente una coincidencia.
- La ocultación QWeb no sustituye el control de acceso en el controlador o modelo.
