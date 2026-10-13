# irg_practice_center_cif

**Categoria:** extrairg
**Version:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Si
**Autor:** IRG
**Depende de:** `isep_practices_2`, `irg_practice_agreement_sign`

---

## Que hace este modulo

Añade el campo CIF a cada centro de practicas. Al generar el contacto, copia ese CIF al VAT del partner. Al crear un convenio nuevo sin NIF/CIF escrito a mano, rellena `center_vat` con el CIF del centro.

## Funcionalidades principales

- Campo `cif` en `practice.center`, visible en el formulario despues de Nombre oficial, en la lista y en la busqueda.
- Generate Center copia el CIF a `res.partner.vat` y, si el centro tiene pais y el contacto no, copia tambien el pais.
- Esa escritura usa el contexto `no_vat_validation`, para que un CIF de texto libre no revierta la creacion del contacto.
- Un convenio creado sin `center_vat` explicito recibe el CIF del centro, aunque el contacto tenga otro VAT.
- Si el convenio ya trae un NIF/CIF, se conserva.
- Si el centro no tiene CIF, el convenio sigue usando el VAT del contacto.

## Diseno tecnico

El modulo hereda `practice.center` y `practice.agreement`. No modifica `isep_practices_2` ni `irg_practice_agreement_sign`.

`resolve_center_cif` devuelve el CIF del centro recortado. Si esta vacio, devuelve el VAT del contacto. El `create` del convenio guarda si el caller paso `center_vat` antes de llamar a `super()`, porque el modulo de firma muta esos valores y mete el VAT del contacto.

## Vistas y UI

- Formulario: `views/practice_center_views.xml`, xpath despues de `official_name`.
- Lista y busqueda: el campo `cif` queda despues de `name`.

## Seguridad

No crea modelos ni endpoints. Reutiliza el acceso de `practice.center` y `practice.agreement`. No usa `sudo()`.

## Instalacion / actualizacion

Con el runtime local en marcha:

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_practice_center_cif \
    --stop-after-init --db_host=pgodoo_local
```

## Pruebas

La resolucion del CIF se prueba sin Odoo:

```bash
python3 addons-extra/extrairg/irg_practice_center_cif/tests/test_resolve_center_cif.py
```

Resultado: `Ran 4 tests` / `OK`.

Las `TransactionCase` del modulo y la capa E2E no se ejecutaron: el daemon de Docker no estaba en marcha.

## Limitaciones conocidas

- No valida el formato del CIF.
- No rellena el alta publica de centros.
- No reescribe convenios ya creados.
- Si mas adelante se edita el VAT o el pais del contacto, `base_vat` puede validar ese CIF.

## Changelog

- 2026-10-13: Creado el modulo `irg_practice_center_cif`.
