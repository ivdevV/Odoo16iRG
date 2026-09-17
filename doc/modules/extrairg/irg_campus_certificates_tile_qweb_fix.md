# irg_campus_certificates_tile_qweb_fix

Addon de herencia que corrige el 500 de `/campus/course/<id>` causado por
`hasattr` en el tile «Certificados y Diplomas».

En Odoo 16, `hasattr` no existe en el evaluador seguro de QWeb. El `t-if`
original llamaba `None(...)` y rompía la plantilla
`isep_website_custom.user_profile_content_details`.

Este módulo sustituye el guard por `not course_id.is_diplomado()`, el mismo
helper que ya usan las tiles de Prácticas y TFM.

`auto_install` es verdadero: se instala solo si ya están
`irg_campus_certificates_portal` e `irg_course_portal_tiles_diplomado_hide`.

No edita `irg_campus_certificates_portal`.
