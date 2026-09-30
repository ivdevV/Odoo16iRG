from odoo import http
from odoo.http import request
from odoo.addons.website_forum.controllers.main import WebsiteForum


class WebsiteForumWebPostBatches(WebsiteForum):

    @http.route(
        [
            '/forum/<model("forum.forum"):forum>/new',
            '/forum/<model("forum.forum"):forum>/<model("forum.post"):post_parent>/reply',
        ],
        type='http',
        auth='user',
        methods=['POST'],
        website=True,
    )
    def post_create(self, forum, post_parent=None, **post):
        if not post_parent and request.env.user.has_group('base.group_user'):
            raw_ids = request.httprequest.form.getlist('irg_visibility_batch_ids')
            batch_ids = forum._irg_sanitize_web_post_batch_ids(raw_ids)
            if batch_ids:
                request.update_context(irg_visibility_batch_ids=batch_ids)
        return super().post_create(forum, post_parent=post_parent, **post)
