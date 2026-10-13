# CIF del centro de practicas

El CIF de un centro de practicas se guarda en `practice.center.cif`. El convenio no debe leer solo `res.partner.vat`.

`irg_practice_agreement_sign` copia `partner_id.vat` a `center_vat` dentro de `create`, mutando el mismo diccionario de valores. Para preferir el CIF del centro hay que recordar, antes de `super()`, si el caller ya paso `center_vat`.

Al copiar el CIF al contacto en Generate Center, el `write` debe ir con `no_vat_validation`. `base_vat` rechaza un NIF sin pais o con un formato que no reconoce y revierte la creacion del partner. El alta original del contacto no rellena `country_id`.
