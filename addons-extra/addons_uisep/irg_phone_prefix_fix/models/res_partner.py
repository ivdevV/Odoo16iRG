# -*- coding: utf-8 -*-
from odoo import models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _phone_format(self, number, country=None, company=None):
        """
        Sobreescribe el formateo para México para preservar el "+52 1" si el usuario lo introdujo.
        """
        # Ejecutar validación estándar primero
        res = super(ResPartner, self)._phone_format(number, country=country, company=company)
        
        if not number or not res:
            return res

        country = country or self.country_id or self.env.company.country_id
        if country and country.code == 'MX':
            # Limpiar entradas para comparación segura
            clean_input = number.replace(" ", "").replace("-", "")
            clean_res = res.replace(" ", "").replace("-", "")

            # Si el input tenía +521...
            if clean_input.startswith("+521"):
                # Y el resultado formateado empieza por +52 pero NO por +521 (lo perdió)
                if clean_res.startswith("+52") and not clean_res.startswith("+521"):
                    # Reconstruir el número añadiendo el 1
                    # Asumimos que res tiene formato "+52 XX..."
                    # Queremos "+52 1 XX..."
                    
                    # Extraer el resto del número después del +52
                    suffix = res[3:].strip()
                    return "+52 1 " + suffix
        
        return res
