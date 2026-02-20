odoo.define('isep_survey.fullscreen', function (require) {
    "use strict";
    
    var core = require('web.core');
    var QWeb = core.qweb;
    var Fullscreen = require('@website_slides/js/slides_course_fullscreen_player')[Symbol.for("default")];
    
    Fullscreen.include({
        _renderSlide: async function () {
            var def = this._super.apply(this, arguments);
            var $content = this.$('.o_wslides_fs_content');
            
            if (this.get('slide').category === "certification") {
                var slide = this.get('slide');
                
                try {
                    const slideData = await this._rpc({
                        route: '/slides/slide/get_slide_data_description',
                        params: { slide_id: slide.id },
                    });
                    
                    slide.slide_description = slideData.slide_description || "";
                    slide.survey_description = this._sanitizeHtmlContent(slideData.survey_description || "");
                    slide.use_html_embed = slideData.use_html_embed;
                    
                } catch (error) {
                    console.error("Error fetching slide data:", error);
                    slide.slide_description = "Descripción no disponible";
                    slide.survey_description = "Contenido no disponible";
                }
                
                $content.html(QWeb.render('website.slides.fullscreen.certification', {
                    widget: this,
                    slide: slide,
                    slide_description: slide.slide_description,
                    survey_description: slide.survey_description,
                    use_html_embed: slide.use_html_embed
                }));
                
                // Ajustar altura del iframe si existe
                this._adjustIframeHeight();
            }
            
            return Promise.all([def]);
        },
        
        /**
         * Sanitiza el contenido HTML para evitar conflictos de estilos
         */
        _sanitizeHtmlContent: function(htmlContent) {
            if (!htmlContent) return "";
            
            // Envolver el contenido en un contenedor aislado
            var wrapped = `
                <div class="embedded-content-wrapper">
                    <style scoped>
                        .embedded-content-wrapper {
                            all: initial;
                            display: block;
                            font-family: inherit;
                        }
                        .embedded-content-wrapper * {
                            box-sizing: border-box;
                        }
                    </style>
                    ${htmlContent}
                </div>
            `;
            
            return wrapped;
        },
        
        /**
         * Ajusta la altura del iframe dinámicamente
         */
        _adjustIframeHeight: function() {
            var self = this;
            setTimeout(function() {
                var $iframe = self.$('#survey-iframe');
                if ($iframe.length) {
                    $iframe.on('load', function() {
                        try {
                            var iframeBody = this.contentDocument || this.contentWindow.document;
                            var height = iframeBody.body.scrollHeight;
                            $(this).height(height + 20);
                        } catch(e) {
                            console.warn('Cannot access iframe content:', e);
                        }
                    });
                }
            }, 100);
        }
    });
});