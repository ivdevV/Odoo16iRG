# -*- coding: utf-8 -*-
from . import controllers

# Monkey-patch del controlador CustomerPortal para añadir valores por defecto a placeholders
from odoo.addons.portal.controllers.portal import CustomerPortal
from .controllers.portal import CustomerPortalPlaceholderCountFix

# Reemplazar la clase original con la versión parcheada
CustomerPortal._prepare_home_portal_values = CustomerPortalPlaceholderCountFix._prepare_home_portal_values
