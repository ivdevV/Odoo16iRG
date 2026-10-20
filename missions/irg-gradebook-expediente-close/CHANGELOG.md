# Cierre de expediente al autocerrar la libreta

## 16.0.1.0.0

- Al autocerrar una libreta, se guarda la fecha de cierre de expediente del
  alumno si estaba vacía.
- En ese mismo caso se avisa a academica@institutoraimongaja.com con alumno,
  correo, curso, admisión, libreta y fecha.
- Un fallo del envío, también un error de base de datos, no deshace el cierre
  ni la fecha.
