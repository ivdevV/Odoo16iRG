from odoo import http
from odoo.http import request
from odoo.addons.isep_survey.controllers.main import SlideController


class SlideControllerAssignment(SlideController):
    
    @http.route('/slides/slide/get_slide_data_description', type='json', auth='user', website=True)
    def get_slide_data(self, slide_id):
        slide = request.env['slide.slide'].sudo().browse(slide_id)
        
        if not slide.exists():
            return {'error': 'Slide not found'}
        
        survey_content = ""
        if slide.use_html_embed and slide.html_embed_code:
            survey_content = slide.html_embed_code
        else:
            survey_content = slide.survey_id.description or ""
        
        return {
            'slide_description': slide.description or '',
            'survey_description': survey_content,
            'use_html_embed': True if slide.use_html_embed else False,
        }