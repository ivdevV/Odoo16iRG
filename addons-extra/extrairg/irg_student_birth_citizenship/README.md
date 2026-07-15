# IRG - Datos de nacimiento y ciudadanía del estudiante

Este módulo añade tres datos personales compartidos entre el contacto de Odoo y el perfil de estudiante de OpenEducat:

- Población de nacimiento (`birth_place`).
- País de nacimiento (`birth_country_id`).
- País de ciudadanía (`citizenship_country_id`).

## Funcionamiento

Los campos se definen y almacenan en `res.partner`. El modelo `op.student` de OpenEducat delega en su contacto mediante `_inherits`, por lo que los mismos campos se pueden leer y editar desde ambos modelos sin copias ni procesos de sincronización.

El campo existente `op.student.nationality` permanece independiente y no se modifica.

## Interfaz

- En el estudiante aparecen después de la fecha de nacimiento, dentro de la información personal.
- En el contacto aparecen en la pestaña **Nacimiento y ciudadanía**.

## Instalación

Instalar o actualizar el módulo técnico `irg_student_birth_citizenship` desde Aplicaciones.

## Pruebas

Las pruebas automatizadas verifican la definición de los campos, la escritura bidireccional contacto/estudiante, su presencia en ambas vistas y la independencia respecto a `nationality`.

## Changelog

### 16.0.1.0.0

- Añadidos los tres campos compartidos de nacimiento y ciudadanía.
- Añadidos los campos a las fichas de estudiante y contacto.
- Añadida cobertura automatizada de modelo, delegación y vistas.
