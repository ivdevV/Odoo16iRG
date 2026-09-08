# irg_practice_agreement_types

**Categoria:** extrairg
**Version:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Si
**Autor:** IRG
**Depende de:** `irg_practice_agreement_sign`

---

## Que hace este modulo

Sustituye el botón «Crear Convenio Marco» del practice center por **Crear Convenio**,
que abre un wizard (radio) para elegir **Convenio Marco Nacional** o
**Convenio Marco Internacional**. El nacional sigue siendo la QWeb del módulo
base. El internacional cambia el bloque de cláusulas (seguros fuera de España,
vigencia/resolución ampliadas, confidencialidad y protección de datos separadas).

## Funcionalidades principales

- Wizard `irg.practice.agreement.create.wizard`.
- Campo `practice.agreement.agreement_type`.
- PDF y portal conmutan cláusulas por tipo. Sin INMIRA ni datos de un centro concreto.
- Guarda server-side: no se cambia el tipo si el convenio está enviado, firmado o cancelado.

## Fuera de alcance

Los convenios específicos (nacional e internacional) están en
`irg_practice_agreement_specific`, no en este módulo.

## Pruebas

```bash
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d test_irg_practice_agreement_types -u irg_practice_agreement_types \
  --test-enable --test-tags /irg_practice_agreement_types \
  --stop-after-init --http-port=8099 --log-level=test
```
