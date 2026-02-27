from odoo import http
from odoo.http import request
from odoo.addons.website_profile.controllers.main import WebsiteProfile
import logging
import pprint

_logger = logging.getLogger(__name__)


class IrgCoursePortalOverrides(WebsiteProfile):
    @http.route(['/campus'], type='http', auth="user", website=True)
    def view_user_profile(self, **post):
        # replicate original behavior but filter out course-level tools
        user_id = request.env.user.id
        user = self._check_user_profile_access(user_id)
        if not user:
            return request.render("website_profile.private_profile")
        values = self._prepare_user_values(**post)
        params = self._prepare_user_profile_parameters(**post)
        values.update(self._prepare_user_profile_values(user, **params))

        menu_list = request.env['openeducat.portal.menu'].sudo().search([
            ('is_visible_to_student', '=', True)
        ])

        def _is_course_tool(menu):
            name = (menu.name or '').lower()
            for kw in ('calendar', 'calendario', 'practic', 'práctic', 'prácticas', 'practica'):
                if kw in name:
                    return True
            return False

        def _is_hidden_global(menu):
            # hide certain global tiles from the /campus dashboard
            name = (menu.name or '').lower()
            for kw in ('curso', 'certific', 'normativ', 'normativa', 'badge', 'insign', 'insignia', 'insignias'):
                if kw in name:
                    return True
            return False

        menu_list = menu_list.filtered(lambda m: not (_is_course_tool(m) or _is_hidden_global(m)))
        values.update({'menu_list': menu_list})

        return request.render("website_profile.user_profile_main", values)

    @http.route(['/campus/course/<int:course_id>'], type='http', auth="user", website=True)
    def view_user_profile_course(self, course_id, **post):
        user_id = request.env.user.id
        user = self._check_user_profile_access(user_id)
        if not user:
            return request.render("website_profile.private_profile")
        values = self._prepare_user_values(**post)
        params = self._prepare_user_profile_parameters(**post)
        values.update(self._prepare_user_profile_values(user, **params))

        values['op_course_id'] = course_id

        # Provide only course-level tools for this view
        menu_list = request.env['openeducat.portal.menu'].sudo().search([
            ('is_visible_to_student', '=', True)
        ])

        def _is_course_tool_local(menu):
            name = (menu.name or '').lower()
            for kw in ('calendar', 'calendario', 'practic', 'práctic', 'prácticas', 'practica'):
                if kw in name:
                    return True
            return False

        def _is_hidden_badge(menu):
            name = (menu.name or '').lower()
            for kw in ('badge', 'insign', 'insignia', 'insignias'):
                if kw in name:
                    return True
            return False

        values['menu_list'] = menu_list.filtered(lambda m: _is_course_tool_local(m) and not _is_hidden_badge(m))

        _logger.info('IRG OVERRIDE values: %s', pprint.pformat(values))
        return request.render("isep_website_custom.user_profile_course", values)
