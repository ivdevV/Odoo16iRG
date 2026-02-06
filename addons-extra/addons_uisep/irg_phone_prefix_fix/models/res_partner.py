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
        
        if not number or not isinstance(number, str):
            return res

        # Intentar resolver el país si no viene dado
        if not country and self:
            country = self.country_id
        if not country and company:
            country = company.country_id
        if not country:
            country = self.env.company.country_id
            
        if country and country.code == 'MX':
            # Limpiar entradas para comparación segura (quitamos espacios, guiones, paréntesis y +)
            # Objetivo: detectar si el usuario escribió la secuencia 521
            clean_input = number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
            
            # Limpiar resultado para verificar si se perdió el 1
            if not res:
                return res
            clean_res = res.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")

            # Si el input tenía 521 al inicio...
            if clean_input.startswith("521"):
                # Y el resultado formateado empieza por 52 pero NO por 521 (el 1 fue eliminado)
                if clean_res.startswith("52") and not clean_res.startswith("521"):
                    # Reconstruir el número añadiendo el 1
                    
                    # Extraer el sufijo del resultado (quitando el +52 inicial)
                    # El formato estándar suele ser +52 XX...
                    # Buscamos dónde termina el +52
                    
                    # Normalizamos res para trabajar más fácil, asegurando que empiece por +52
                    temp_res = res.lstrip("+")
                    if temp_res.startswith("52"):
                        suffix = temp_res[2:].strip() # Lo que sigue al 52
                        return "+52 1 " + suffix
        
        return res
