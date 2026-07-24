# Diseño: resolución de actividades Moodle por `iteminstance`

## Problema confirmado

Los valores de `Moodle IDs List` del CSV de asignaturas representan el
identificador de instancia de la actividad Moodle. El servicio
`gradereport_user_get_grade_items` lo devuelve como `iteminstance`.

En una consulta real del curso Moodle 35 se confirmó, por ejemplo:

- CSV: `205`.
- Respuesta Moodle: `id=555`, `cmid=3290`, `iteminstance=205`,
  `itemmodule=quiz`.

El sincronizador actual solo compara el valor importado con `id` y `cmid`.
Por ello informa cero coincidencias aunque la actividad exista. El soporte de
múltiples ediciones HomeClass sí funciona: el asistente consulta los cursos 35
y 36, pero ambos aplican la resolución incompleta.

## Alcance

El cambio debe:

1. Admitir que un ID configurado coincida con `id`, `cmid` o
   `iteminstance`.
2. Exigir exactamente un grade item resultante.
3. Mantener la comprobación de `itemmodule` frente al tipo configurado
   (`quiz` o `assign`).
4. Mantener el rechazo cuando dos líneas de mapeo terminan usando el mismo
   grade item.
5. Aplicarse tanto al flujo base como al selector de múltiples HomeClass.
6. Distinguir en el mensaje de diagnóstico entre cero coincidencias y varias
   coincidencias.
7. No exigir modificar ni volver a importar los CSV existentes.

Quedan fuera de alcance cambios en el modelo de mapeo, nuevas columnas CSV,
normalización por nombre y selección automática por edición académica.

## Alternativas consideradas

### Recomendada: aceptar los tres espacios de ID durante la resolución

La resolución compara cada valor configurado con `id`, `cmid` e
`iteminstance`, deduplica por grade item y exige un único resultado.

Ventajas: corrige los datos ya importados, no necesita llamadas Moodle
adicionales y conserva compatibilidad con mapeos antiguos basados en `id` o
`cmid`.

### Convertir los IDs durante la importación

La importación consultaría Moodle para transformar `iteminstance` a `id` o
`cmid`.

Se descarta porque acopla la importación a la disponibilidad del servicio,
obliga a reprocesar datos existentes y añade permisos y errores de red.

### Guardar explícitamente el tipo de identificador

Cada línea indicaría si contiene `id`, `cmid` o `iteminstance`.

Se descarta para este arreglo porque requiere cambios de modelo, vistas, CSV y
migración sin aportar valor al conjunto de datos actual.

## Diseño técnico

Se incorporará un resolvedor único y reutilizable que reciba los grade items y
un ID configurado. Un item será candidato si cualquiera de sus campos `id`,
`cmid` o `iteminstance` coincide exactamente con ese valor.

El resolvedor trabajará con la posición real del item en la respuesta para no
contar dos veces el mismo objeto si, excepcionalmente, el mismo número aparece
en dos campos del propio item. Sus resultados serán:

- un candidato: resolución válida;
- ningún candidato: actividad no encontrada;
- más de un candidato: resolución ambigua.

Después se ejecutan sin cambios las validaciones de tipo, reutilización de un
mismo grade item, nota numérica y escala. El addon de múltiples HomeClass
considerará recuperable una actividad no encontrada y probará la siguiente
edición; una resolución ambigua o un tipo incompatible seguirá bloqueando esa
edición.

La validación del payload Moodle reconocerá `iteminstance` como entero o nulo,
igual que los identificadores ya admitidos. Se permite el valor cero porque
Moodle lo utiliza en grade items que no representan una actividad.

## Compatibilidad y errores

Los mapeos existentes que usan `id` o `cmid` seguirán funcionando. Si un número
coincide con items diferentes a través de espacios de ID distintos, el sistema
no elegirá arbitrariamente: mostrará una incompatibilidad por resolución
ambigua.

Los diagnósticos mostrarán:

- `no se encontró por id/cmid/iteminstance` para cero coincidencias;
- `resolución ambigua` con el número de candidatos para más de una.

## Pruebas y aceptación

La implementación seguirá TDD y deberá cubrir:

1. RED/GREEN de coincidencia exclusiva por `iteminstance`.
2. Compatibilidad por `id` y por `cmid`.
3. Un mismo item que coincide por dos de sus campos cuenta una sola vez.
4. Colisión entre items distintos continúa siendo incompatible.
5. `itemmodule` incorrecto continúa siendo incompatible.
6. Payload con `iteminstance` inválido se rechaza.
7. El fallback HomeClass encuentra una actividad por `iteminstance` en
   cualquiera de las ediciones.
8. Cero coincidencias en una edición permite probar la siguiente.
9. Las suites completas de los addons base y HomeClass permanecen verdes.

El criterio funcional final es que los IDs reales del CSV, como `205`, resuelvan
el grade item cuyo `iteminstance` es `205` sin cambiar el mapeo importado.
