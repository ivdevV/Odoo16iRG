# Changelog — Gradebook Template Precedence Fix

## Added

- Extensión por `_inherit` de `app.gradebook.subject.compute_data_show()` para
  calcular las categorías efectivas de cada línea.
- Nueve regresiones ORM: ocho para la precedencia de Asignaciones, Exámenes,
  Interacciones y Foro, y una para valores `show_*` stored anteriores al upgrade.
- Documentación reusable del caso reproducido en Dev y del patrón de intersección.

## Fixed

- El template de una asignatura ya no puede añadir requisitos ausentes en el template
  principal de la libreta.
- Una libreta `Solo Examen` deja de quedar bloqueada por una asignatura cuyo template
  interno mixto incluya Asignaciones.
- Se conservan las excepciones en las que el template de línea elimina requisitos del
  template principal.
- Antes de evaluar el autocierre, el trigger refresca la visibilidad stored de las
  líneas de la libreta afectada; un valor obsoleto anterior al upgrade ya no bloquea
  una libreta `Solo Examen`.

## Tested

- Suite completa del addon ejecutada con `docker-compose.local.yml` contra
  `test_irg_db`: 22 tests, 0 fallos y 0 errores; proceso finalizado con código 0.
- La regresión stale-store fuerza `show_assignment=True` en almacenamiento y
  comprueba que un `write` del resultado lo refresca a `False` antes de cerrar.
- Comprobados imports, manifest, sintaxis de los ocho archivos Python y ausencia de
  cambios en `isep_gradebook`.
- `missions/fix-gradebook-template-precedence/verification.json` registra estado
  `passed` y enlaza las evidencias de validación.

## Limitations

- Instalar o actualizar el addon no barre ni cierra retroactivamente las libretas ya
  existentes; una mutación posterior de `app.gradebook.result` refresca solo la
  libreta afectada.
- Si falta el template principal, se conserva el cálculo base de `isep_gradebook`.
- No se han realizado commit, push, despliegue, SSH ni cambios sobre el servidor Dev.
