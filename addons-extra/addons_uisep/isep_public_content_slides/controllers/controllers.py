from odoo import http
from odoo.http import request, Response
import json

class CourseController(http.Controller):
    
    @http.route('/json/courses', auth='public', type='http', website=True)
    def get_courses(self):
        courses = request.env['op.course'].sudo().search([('include_txt', '=', True)])
        
        course_data = []        
                       
        for content in courses:
            course_data.append({
                "id": content.id,
                "name": content.name,
                "course_url": f"{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/json/courses/{content.id}",
            })
        return Response(
            json.dumps(course_data),
            content_type='application/json',
            status=200
        )

    @http.route('/json/courses/<int:course_id>', auth='public', type='http',  website=True)
    def get_course_content(self, course_id):
        course = request.env['op.course'].sudo().browse(course_id)
        if not course:
            return {"error": "Course content not found"}
        if not course.include_txt:
            return {"error": "Course content restrict"}
        

        course_data = []
        concatenated_html_content = []
        for subject in course.sudo().subject_ids:
           
            content_lines = subject.sudo().line_ids
            
            if content_lines:
                for line in content_lines:
                    concatenated_html_content.append({
                        'name': line.name,
                        'content': line.html_content
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
        
