# irg_practice_agreement_specific

**Categoria:** extrairg
**Version:** 16.0.1.1.0
**Licencia:** LGPL-3
**Instalable:** Si
**Autor:** IRG
**Depende de:** `irg_practice_agreement_types`

---

## Que hace este modulo

Añade **Crear Convenio** en la solicitud de prácticas (`practice.request`).
El wizard (radio) crea un **Convenio Específico Internacional** o un
**Convenio Específico Nacional** ligado a la solicitud y al centro
asignado, con copia de alumno, máster, documento, fechas, días, horario,
horas y tutor.

La firma es triple: iRG precargada; el centro firma en
`/convenio/firma/<token>` y el estudiante en
`/convenio/firma-alumno/<token>`. El estado pasa a firmado solo cuando
existen las dos firmas.

## Excepción de módulo

El nacional **no** tiene un módulo propio. Se añadió en este addon
(16.0.1.1.0) como **excepción explícita y acotada** a la regla de no
editar módulos existentes: wizard, doble firma y PDF son los mismos; un
módulo nuevo solo para la variante no tiene sentido. La excepción **no**
sienta precedente para tocar `irg_practice_agreement_sign` ni
`irg_practice_agreement_types`.

## Funcionalidades principales

- Wizard `irg.practice.agreement.specific.create.wizard` (Internacional /
  Nacional).
- `practice.agreement.agreement_type`: valores `especifico_internacional`
  y `especifico_nacional`. `_is_especifico()` cubre ambos.
- Tokens distintos para centro y alumno. Dos plantillas de correo.
- PDF y portal conmutan el cuerpo del marco por el documento del tipo.
- Internacional: QUINTA deja la RC de iRG solo en España; Anexo I.
- Nacional: QUINTA = RC, accidentes personales y asistencia sanitaria a
  cargo de iRG (sin «fuera de España»); normativa con ley 26/2015.
- El bloque de actividades propuestas por el alumno solo se pinta si hay
  texto.

## Fuera de alcance

Lugar de prácticas distinto del centro asignado. Flujo legado de Odoo
Sign. No se editan `irg_practice_agreement_sign` ni
`irg_practice_agreement_types`.

## Pruebas

```bash
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d test_irg_practice_agreement_specific -u irg_practice_agreement_specific \
  --test-enable --test-tags /irg_practice_agreement_specific \
  --stop-after-init --http-port=8099 --log-level=test
```
