# Patron: overlay de ir.actions.report ajeno y print_report_name

Fecha: 2026-09-04

Modulo: `irg_practice_agreement_types`

## Decision reutilizable

Si un módulo nuevo debe cambiar `print_report_name` de un `ir.actions.report`
cuyo xml_id pertenece a otro módulo, la expresión tiene que ser defensiva:

```python
'agreement_type' in object._fields and object.agreement_type == 'marco_internacional'
```

El xml_id no cambia de módulo. Al desinstalar el override, el valor **persiste**
en el registro base. Una expresión que lea el campo nuevo a ciegas lanza
`AttributeError` al imprimir.

En QWeb no usar `hasattr` (no está en safe_eval de plantillas). En
`print_report_name` (eval de servidor) `object._fields` sí es válido.

Si varios módulos overlayan el **mismo** `xml_id` de `ir.actions.report`,
gana el último en el grafo de dependencias. El módulo posterior debe
**repetir todas las ramas** anteriores en `print_report_name` (con la
guarda `_fields`). Un `-u` aislado del módulo anterior revierte la
expresión a la suya.
