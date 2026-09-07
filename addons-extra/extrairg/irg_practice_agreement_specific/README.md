# IRG Practice Agreement Specific

En la **solicitud de prácticas** del alumno, **Crear Convenio** abre un
wizard para generar un **Convenio Específico Internacional** (anexo al
marco) con el centro asignado.

## Uso

1. Instalar `irg_practice_agreement_specific` (depende de
   `irg_practice_agreement_types`).
2. Abrir una solicitud con centro asignado → **Crear Convenio**.
3. Opcionalmente rellenar «Actividades propuestas por el alumno».
4. **Crear**. Se abre el convenio en borrador con los datos copiados.
5. **Enviar por Email**: salen dos correos (centro y estudiante), cada uno
   con su enlace de firma.
6. El PDF se genera cuando **ambas** partes han firmado (iRG va
   precargada). Se adjunta al convenio, a la solicitud y al centro.

El específico nacional no está en esta entrega.

## Pruebas

```bash
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d <db> -u irg_practice_agreement_specific \
  --test-enable --test-tags /irg_practice_agreement_specific \
  --stop-after-init --http-port=8099 --log-level=test
```
