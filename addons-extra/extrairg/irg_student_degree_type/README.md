# IRG - Tipo de titulación del estudiante

Añade en la ficha de alumno (`op.student`) el campo **Tipo de titulación**,
con el widget de etiquetas de color (`many2many_tags`).

## Uso

1. Instalar el módulo `irg_student_degree_type`.
2. Abrir un alumno → pestaña Información personal.
3. Bajo **Contacto de emergencia** (y, si existe en esa columna, bajo
   **Estado de pago**) aparece **Tipo de titulación**.
4. Escribir o elegir una etiqueta. El color se elige en el catálogo
   *OpenEduCat → Configuración → Tipos de titulación*.

Este campo clasifica el **tipo** (p. ej. título propio, máster
universitario). No sustituye `titulacion` / `x_studio_titulacion` /
`study_type_id`, que guardan la titulación concreta.

## Seguridad

- Lectura: usuarios internos.
- Crear y escribir: back-office OpenEduCat.
- Borrar: back-office admin (en la práctica el grupo back-office implica
  admin en esta instancia).

## Pruebas

```bash
odoo -d <db> -i irg_student_degree_type --test-enable \
  --test-tags /irg_student_degree_type --stop-after-init
```
