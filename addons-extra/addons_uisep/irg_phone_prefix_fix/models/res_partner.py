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
            
        # Detectar si estamos tratando con un número mexicano
        # 1. Por el país explícito
        is_mexico = country and country.code == 'MX'
        
        if not is_mexico and res and res.startswith('+52'):
            # 2. Por el resultado formateado (que ya identificó el país)
            is_mexico = True
            
        if is_mexico:
            # Limpiar entradas para comparación segura (quitamos espacios, guiones, paréntesis y +)
            # Objetivo: detectar si el usuario escribió la secuencia 521 al principio o +52 1
            clean_input = number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
            
            # Limpiar resultado para verificar si se perdió el 1
            if not res:
                return res
            clean_res = res.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")

            # Si el input original tenía 521...
            # OJO: clean_input podría no tener el 52 si el usuario puso solo "1 55..." y el país era MX.
            # Pero si el usuario puso +52 1 ..., clean_input empieza por 521.
            
            user_typed_one = False
            if clean_input.startswith("521"):
                user_typed_one = True
            elif country and country.code == 'MX' and clean_input.startswith("1"):
                # Caso usuario escribe "1 55 1234 5678" asumiendo prefijo local
                user_typed_one = True

            if user_typed_one:
                # Y el resultado formateado empieza por 52 pero NO por 521 (el 1 fue eliminado)
                # Ejemplo clean_res: 525512345678
                if clean_res.startswith("52") and not clean_res.startswith("521"):
                    # Reconstruir el número añadiendo el 1
                    
                    # Normalizamos res para trabajar más fácil, asegurando que empiece por +52
                    temp_res = res.lstrip("+")
                    if temp_res.startswith("52"):
                        suffix = temp_res[2:].strip() # Lo que sigue al 52
                        return "+52 1 " + suffix
        
        return res
