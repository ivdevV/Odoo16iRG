# Micro-spec: precedencia efectiva de templates en autocierre de libreta

## Problema reproducido

En Dev, la libreta `AD003762` muestra como template principal `Solo Examen` y todas
sus líneas tienen examen y calificación final mayores que cero. Sin embargo, una línea
conserva internamente el template de asignatura `1 Asignación 1 Examen`. El autocierre
consulta `show_assignment` de esa línea, exige una asignación que el template principal
no contempla y deja la libreta en `in_progress`.

## Regla aprobada

Los requisitos efectivos de cada línea son la intersección entre:

1. las categorías presentes en el template principal de la libreta; y
2. las categorías presentes en el template específico de la línea, cuando exista.

Por tanto, una línea puede eliminar un requisito del template principal —por ejemplo,
Prácticas o TFM pueden omitir Asignaciones—, pero nunca añadir un requisito ausente en
el template principal.

Formalmente, para `exam`, `assignment`, `interaction` y `foro`:

```text
requisito_efectivo = requisito_template_libreta AND requisito_template_linea
```

Si la línea no tiene template específico, hereda el requisito del template principal.

## Diseño

El módulo existente `irg_gradebook_auto_close` extenderá
`app.gradebook.subject.compute_data_show()` mediante `_inherit` y, después de la lógica
base, ajustará los cuatro campos `show_*` con la intersección aprobada. No se modificará
`isep_gradebook`.

El autocierre seguirá usando `_irg_is_ready_to_close()` y `state_to_done()`. Al quedar
`show_assignment=False` para una libreta `Solo Examen`, tanto la condición previa como
la validación existente omitirán correctamente Asignaciones.

Como los campos `show_*` son computes almacenados y pueden conservar valores calculados
antes de actualizar el módulo, `_irg_try_auto_close()` refrescará `compute_data_show()`
solo en las líneas de la libreta afectada antes de evaluar la condición. Esto permite
que una nueva escritura de nota corrija datos almacenados obsoletos sin hacer un barrido
global ni cerrar libretas durante la actualización.

## Casos de aceptación

1. Libreta `Solo Examen` + línea interna `Asignación y Examen` + examen/final positivos:
   la línea no exige asignación y la libreta se cierra.
2. Libreta `Asignación y Examen` + línea normal con el mismo template: exige ambos.
3. Libreta `Asignación y Examen` + línea especial `Solo Examen`: omite asignación.
4. Línea sin template específico: hereda las categorías del template principal.
5. La suite completa existente continúa pasando.
6. Una línea con `show_assignment=True` almacenado antes de la actualización se
   recalcula al escribir una nota y la libreta se cierra si el template efectivo es
   `Solo Examen`.

## Fuera de alcance

- Barrido retroactivo de libretas antiguas al instalar o actualizar el módulo.
- Modificar datos de templates u `op.subject` en Dev.
- Cierre directo mediante `state = "done"`.
- Cambios en módulos existentes.
- Commit o push remoto sin autorización explícita posterior.
