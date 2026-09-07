# irg_practice_agreement_specific

**Categoria:** extrairg
**Version:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Si
**Autor:** IRG
**Depende de:** `irg_practice_agreement_types`

---

## Que hace este modulo

Añade **Crear Convenio** en la solicitud de prácticas (`practice.request`).
El wizard crea un **Convenio Específico Internacional** ligado a la solicitud
y al centro asignado, con copia de alumno, máster, documento, fechas, días,
horario, horas y tutor.

La firma es triple: iRG precargada; el centro firma en
`/convenio/firma/<token>` y el estudiante en
`/convenio/firma-alumno/<token>`. El estado pasa a firmado solo cuando
existen las dos firmas. El PDF (cláusulas Primera–Séptima y Anexo I) no
incluye INMIRA ni un área concreta; la QUINTA deja la RC de iRG solo en
España. El bloque de actividades propuestas por el alumno solo se pinta
si hay texto.

## Funcionalidades principales

- Wizard `irg.practice.agreement.specific.create.wizard`.
- `practice.agreement.agreement_type`: valor `especifico_internacional`.
- Tokens distintos para centro y alumno. Dos plantillas de correo.
- PDF y portal conmutan el cuerpo del marco por el documento específico.

## Fuera de alcance

Convenio específico nacional (cuando exista ejemplo). Lugar de prácticas
distinto del centro asignado. Flujo legado de Odoo Sign.

## Pruebas

```bash
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d test_irg_practice_agreement_specific -u irg_practice_agreement_specific \
  --test-enable --test-tags /irg_practice_agreement_specific \
  --stop-after-init --http-port=8099 --log-level=test
```
