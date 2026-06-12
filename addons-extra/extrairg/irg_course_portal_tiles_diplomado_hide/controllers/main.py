# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.irg_course_portal_tiles.controllers.main import IrgTFMController


class IrgTFMControllerDiplomado(IrgTFMController):
    """
    Controller override to restrict TFM page access for Diplomado courses.
    """

    @http.route(['/campus/course/<int:course_id>/tfm'], type='http', auth='user', website=True)
    def tfm_page(self, course_id, **kwargs):
        """
        If course.is_diplomado() is True, return request.render('website.403').
        Else, delegate to super.
        """
        course = request.env['op.course'].sudo().browse(course_id)
        if course.exists() and course.is_diplomado():
            return request.render('website.403')
        return super(IrgTFMControllerDiplomado, self).tfm_page(course_id, **kwargs)
