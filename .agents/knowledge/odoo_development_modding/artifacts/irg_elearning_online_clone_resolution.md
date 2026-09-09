# Resolución segura de clones eLearning Online

## Contexto

Algunos canales eLearning HomeClass/Online mantienen una relación en ambos
sentidos, pero los datos históricos pueden conservar únicamente el enlace del
clon Online hacia su canal HomeClass de origen. Un puntero ausente no implica que
el clon correcto pueda elegirse por semejanza de nombre, etiquetas o relaciones
transitivas.

## Patrón probado

1. Tome el canal HomeClass configurado como base.
2. Acepte el puntero directo al clon solo si no es un autorenlace y el clon apunta
   de vuelta a esa misma base.
3. Si el directo falta o es inválido, busque exclusivamente clones cuyo campo de
   origen sea exactamente la base.
4. Excluya la propia base y limite la consulta a dos filas: solo una coincidencia
   es válida; cero o dos indican configuración ausente o ambigua.
5. No amplíe componentes transitivos para seleccionar el canal efectivo. Los
   candidatos no elegidos tampoco deben incorporarse a la familia autorizada.

Este patrón preserva compatibilidad con datos asimétricos y mantiene el acceso
fail-closed ante autorenlaces, inconsistencias y duplicados.

## Edición de categorías espejadas

Un Many2many calculado usado para mostrar secciones de otro canal suele ser de
solo lectura. Cuando el operador necesita editar un atributo de esas categorías,
puede exponerse un One2many relacionado filtrado a categorías existentes. La
vista espejo debe impedir creación y borrado y dejar de solo lectura título,
canal, jerarquía, lotes, fechas y publicación.

La restricción visual no es suficiente: el modelo debe rechazar en servidor los
cambios del campo protegido realizados por usuarios externos. Así se evita que
una llamada RPC directa eluda el formulario restringido.
