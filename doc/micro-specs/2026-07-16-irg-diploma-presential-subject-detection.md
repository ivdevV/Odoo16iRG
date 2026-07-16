# Micro-spec: detección del módulo presencial

## Problema

El cálculo 50/50 está activo, pero retorna al promedio estándar porque no
identifica el módulo presencial aunque la línea visible contenga ese texto.

## Solución

Un addon puente revisará tanto el nombre interno de la asignatura como el nombre
almacenado de la línea y reconocerá la frase normalizada `modulo presencial`
con límites de palabra, admitiendo prefijos y sufijos.

## Aceptación

- El caso beta deja de registrar cero candidatos.
- 6 x 10 y presencial 8,44 producen 9,22.
- Se mantiene la exigencia de un único candidato presencial.
