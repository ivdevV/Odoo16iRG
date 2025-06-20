# knowledge_content.py
from odoo import models, fields, api
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import io
import base64
import logging
_logger = logging.getLogger(__name__)


class OpSubject(models.Model):
    _inherit = 'op.subject'

    line_ids = fields.One2many('subject.content.line', 'subject_id', string="Content Lines")
     
    def sync_slide_to_txt(self, limit):
        for record in self:
            slides = record.slide_channel_id.slide_ids.filtered(
                lambda sld: (  
                    (not sld.content_line_id or sld.update_txt_slide == True) and sld.slide_category in ['article', 'document'] 
                    and sld.is_published == True and sld.is_category == False 
                )
            )[:limit]
            
            record.line_ids.filtered(lambda content: content.slide_id == False ).unlink()
            for slide in slides:
                name = slide.with_context(lang='es_MX').name or slide.name
                if not slide.content_line_id:
                    content_line_id = record.env['subject.content.line'].create({
                        'name': name,
                        'subject_id': record.id,
                        'slide_id': slide.id,
                    })
                    slide.content_line_id = content_line_id                    
                else:
                    #if slide.content_line_id.subject_id.id == record.id:                    
                    content_line_id = slide.content_line_id
                    content_line_id.name = name
                content_line_id.update_txt(slide)


      
                
    
