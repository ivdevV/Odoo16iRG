# IRG Cierre de expediente al autocerrar la libreta

Cuando el autocierre de `irg_gradebook_auto_close` deja una libreta en
Finalizado, este módulo escribe la fecha de hoy en **Fecha cierre de
expediente** del alumno, si ese campo está vacío, y avisa a académica.

## Qué hace

1. Toma las libretas en proceso cuyo alumno no tiene fecha.
2. Deja que el autocierre existente las finalice.
3. Si la libreta quedó en Finalizado y la fecha sigue vacía, guarda la fecha
   de hoy y envía un correo.

El destinatario es siempre `academica@institutoraimongaja.com`. El asunto es
`CIERRE DE EXPEDIENTE: <alumno> — <número de admisión> — <curso>`. El cuerpo
abre con ese mismo título y lleva alumno, correo del alumno, curso, admisión,
libreta y la fecha en
formato `dd/MM/yyyy`. El mensaje queda en el historial de la libreta.

Pulsar Finalizar a mano no escribe la fecha ni envía el correo.

## Instalación

Depende de `irg_gradebook_auto_close`, `isep_gradebook`, `isep_student_filter`
y `mail`. No recorre libretas que ya estaban finalizadas.

La plantilla es **Cierre de expediente — Aviso a académica**. Se puede editar
el texto. El código sigue forzando el destinatario.

## Límites

- Una fecha por alumno. La segunda libreta del mismo alumno no la pisa ni
  vuelve a avisar.
- Si el envío falla, la libreta sigue finalizada, la fecha se conserva y el
  error queda en el log. Este módulo no reintenta el aviso.
- No genera diploma ni certificado.
- Reabrir la libreta no borra la fecha.
