# IRG Practice Agreement Specific

En la **solicitud de prácticas** del alumno, **Crear Convenio** abre un
wizard (radio) para generar un **Convenio Específico Internacional**,
**Nacional** o **HomeClass Síncronas** (anexo al marco) con el centro
asignado.

## Excepción de módulo

Las tres variantes viven **en este mismo módulo** (no hay addons
hermanos). Es una excepción autorizada a la regla de no editar módulos
existentes: un módulo nuevo no aportaría arquitectura, solo duplicaría
wizard, doble firma e informe. La excepción **no** autoriza editar
`irg_practice_agreement_sign` ni `irg_practice_agreement_types`.

## Uso

1. Instalar `irg_practice_agreement_specific` (depende de
   `irg_practice_agreement_types`).
2. Abrir una solicitud con centro asignado → **Crear Convenio**.
3. Elegir Internacional, Nacional o HomeClass Síncronas.
4. Opcionalmente rellenar «Actividades propuestas por el alumno».
5. **Crear**. Se abre el convenio en borrador con los datos copiados.
6. **Enviar por Email**: salen dos correos (centro y estudiante), cada uno
   con su enlace de firma.
7. El PDF se genera cuando **ambas** partes han firmado (iRG va
   precargada). Se adjunta al convenio, a la solicitud y al centro.

El nacional cubre RC, accidentes y asistencia sanitaria a cargo de iRG
(sin «fuera de España») y cita la ley 26/2015. El internacional
mantiene la RC de iRG solo en España. El HomeClass síncronas no cubre
seguros en QUINTA (esa cláusula es la rescisión); la SEXTA permite que
el centro cobre a pacientes y deja el alumno sin remuneración.

## Pruebas

```bash
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d <db> -u irg_practice_agreement_specific \
  --test-enable --test-tags /irg_practice_agreement_specific \
  --stop-after-init --http-port=8099 --log-level=test
```
