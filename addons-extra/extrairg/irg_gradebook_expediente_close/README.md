# IRG Cierre de expediente al cerrar la libreta

Cuando una libreta pasa a Finalizado por el ORM, este módulo escribe la fecha
de hoy en **Fecha cierre de expediente** del alumno, si ese campo está vacío, y
avisa a académica.

## Qué hace

1. En un `write` que pone `state` en `done`, toma las libretas que aún no estaban
   finalizadas y cuyo alumno no tiene fecha.
2. Deja que el `write` de Odoo, el botón Finalizar o la API terminen el cambio.
3. Si la libreta quedó en Finalizado y la fecha sigue vacía, guarda la fecha
   de hoy y envía un correo.

Ese `write` es el camino del autocierre, del botón **Cerrar Libreta**, de la
barra de estado y de una llamada API o MCP que ejecute `state_to_done` o
`write` con `state = done`.

El destinatario es siempre `academica@institutoraimongaja.com`. El asunto es
`CIERRE DE EXPEDIENTE: <alumno> — <número de admisión> — <curso>`. El cuerpo
abre con ese mismo título y lleva alumno, correo del alumno, curso, admisión,
libreta y la fecha en formato `dd/MM/yyyy`. El mensaje queda en el historial
de la libreta.

## Instalación

Depende de `irg_gradebook_auto_close`, `isep_gradebook`, `isep_student_filter`
y `mail`. Actualizar a `16.0.1.1.0` no recorre libretas que ya estaban
finalizadas.

La plantilla es **Cierre de expediente — Aviso a académica**. Se puede editar
el texto. El código sigue forzando el destinatario.

## Límites

- Una fecha por alumno. La segunda libreta del mismo alumno no la pisa ni
  vuelve a avisar.
- Si el envío falla, la libreta sigue finalizada, la fecha se conserva y el
  error queda en el log. Este módulo no reintenta el aviso.
- No genera diploma ni certificado.
- Reabrir la libreta no borra la fecha. Cerrarla otra vez no envía otro correo.
- Crear la libreta ya en Finalizado, o cambiar el estado con SQL, no avisa.
