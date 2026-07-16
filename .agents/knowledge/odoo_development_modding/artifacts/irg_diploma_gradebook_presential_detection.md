# Detección robusta de asignaturas presenciales en libretas Odoo

## Diagnóstico reutilizable

El warning `found 0 presential subject candidates` demuestra que el motor de
ponderación sí se ejecutó y que el modo de plantilla ya pasó sus validaciones
anteriores. En ese escenario no se debe seguir investigando el selector ni la
MRO: la causa está acotada a los datos o al helper que identifica las líneas.

En `app.gradebook.subject` pueden coexistir dos etiquetas distintas:

- `op_subject_id.name`, nombre actual de la asignatura relacionada; y
- `name`, texto almacenado de la línea que puede ser el que ve el usuario.

El patrón `related.name or line.name` es incorrecto para detección: no expresa
fallback semántico, sino cortocircuito. Si el primer texto existe pero no
coincide, el segundo nunca se inspecciona. Esto explica que la interfaz muestre
`AD003983 - Modulo presencial` mientras el helper devuelve falso.

## Patrón aplicado

- Evaluar de forma independiente todos los campos que puedan contener la
  etiqueta funcional.
- Normalizar cada candidato antes de compararlo.
- Buscar la frase completa con límites de palabra, no anclarla al final si el
  negocio permite prefijos o sufijos descriptivos.
- Mantener la cardinalidad estricta: exactamente un candidato presencial.
- Extender el helper en un addon puente cargado después de la cadena existente,
  sin modificar el addon original.

Patrón conceptual:

```python
candidate_names = (line.op_subject_id.name, line.name)
return any(
    re.search(r'(?<!\w)modulo presencial(?!\w)', normalize(name))
    for name in candidate_names
    if name
)
```

Los límites negativos evitan falsos positivos como `presencialidad` o
`supermodulo`, mientras permiten `Modulo presencial - Certificacion`.

## Regresión mínima

1. Nombre interno con prefijo y sufijo: debe coincidir.
2. Nombre interno sin coincidencia y nombre visible válido: debe coincidir.
3. Frases parciales: no deben coincidir.
4. Caso funcional 6 x 10 + presencial 8,44: debe dar 9,22.
5. Dos candidatos: el helper de ponderación debe devolver falso y conservar el
   fallback seguro.

## Gotchas operativos

- Un nombre visible correcto no garantiza que `op_subject_id.name` sea igual.
- Los campos computados almacenados solo se recalculan cuando cambia alguna de
  sus dependencias declaradas. Si el nombre visible no forma parte del
  `@api.depends` previo, cambiar y volver a guardar `gradebook_id` es una forma
  acotada de forzar el recálculo.
- Instalar código Python requiere que todos los workers carguen el registro
  actualizado; desplegar archivos sin reiniciar puede conservar clases viejas.
- Cero candidatos y múltiples candidatos son fallos estructurales distintos,
  pero ambos deben mantener el cálculo heredado en lugar de elegir una línea de
  manera arbitraria.

## Resultado validado

`irg_diploma_gradebook_presential_detection` pasó cinco pruebas Odoo
post-install con `docker-compose.local.yml`: 5 superadas, 0 fallos, 0 errores.
El caso beta reproducido produjo `total_final = avg_score = 9,22` y la
instalación terminó con código 0.
