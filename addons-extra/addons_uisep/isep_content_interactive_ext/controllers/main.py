from odoo import http
from odoo.http import request, Response
import json

from odoo.addons.isep_public_content_slides.controllers.controllers import CourseController


class CourseControllerInh(CourseController):


    @http.route('/json/courses/<int:course_id>', auth='public', type='http',  website=True)
    def get_course_content(self, course_id):
        course = request.env['op.course'].sudo().browse(course_id)
        if not course:
            return Response(
                json.dumps({"error": "Course content not found"}),
                content_type='application/json',
                status=200
            )
             
        if not course.include_txt:
            return Response(
                json.dumps({"error": "Course content restrict"}),
                content_type='application/json',
                status=200
            )
            
        

        course_data = []
        concatenated_html_content = []
        for subject in course.sudo().subject_ids:           
            
            if subject.slide_channel_id:
                for slide in subject.slide_channel_id.slide_ids:
                    if slide.content_line_id:
                        concatenated_html_content.append({
                            'name': slide.content_line_id.name,
                            'content': slide.content_line_id.html_content if not slide.use_html_embed else slide.html_code_text
                        })

                # concatenated_html_content = " ".join(content_lines.mapped('html_content'))
               
            
            course_data.append({
                    "id": subject.id,
                    "name": subject.name,
                    "details": concatenated_html_content,
                })
            concatenated_html_content = []
        return Response(
            json.dumps(course_data),
            content_type='application/json',
            status=200
        )