# -*- coding: utf-8 -*-
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalPlaceholderCountFix(CustomerPortal):
	"""Extiende `portal.CustomerPortal` para asegurar valores por defecto
	en los placeholders usados por los badges del portal.

	Evita que el JS del portal intente actualizar elementos con `null`.
	"""

	def _prepare_home_portal_values(self, counters):
		values = super(CustomerPortalPlaceholderCountFix, self)._prepare_home_portal_values(counters)

		# Rellenar los valores por defecto solicitados por `counters`
		if isinstance(counters, (list, tuple, set)):
			for placeholder in counters:
				if values.get(placeholder) is None:
					values[placeholder] = 0

		# Asegurar claves conocidas que el portal puede actualizar
		placeholder_keys = [
			'documents_quantity',
			'documents_count',
			'quotation_count',
			'order_count',
		]
		for placeholder in placeholder_keys:
			if values.get(placeholder) is None:
				values[placeholder] = 0

		return values

