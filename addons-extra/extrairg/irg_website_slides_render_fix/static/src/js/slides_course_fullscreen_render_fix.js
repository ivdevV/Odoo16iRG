odoo.define('irg_website_slides_render_fix.fullscreen_render_fix', function (require) {
    'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var QWeb = core.qweb;
    var Quiz = require('@website_slides/js/slides_course_quiz').Quiz;
    var Fullscreen = require('@website_slides/js/slides_course_fullscreen_player')[Symbol.for('default')];
    var unhideConditionalElements = require('@website/js/content/inject_dom').unhideConditionalElements;
    var _t = core._t;

    var previousRenderSlide = Fullscreen.prototype._renderSlide;

    Fullscreen.include({
        _renderSlide: async function () {
            var slide = this.get('slide');
            var handledCategory = slide && _.contains([
                'quiz',
                'certification',
                'document',
                'infographic',
                'local_external',
                'bunny',
                'scorm',
                'article',
            ], slide.category);
            var handledVideo = slide && slide.category === 'video' && slide.videoSourceType === 'google_drive';

            if (!slide || (!slide.isQuiz && !handledCategory && !handledVideo)) {
                return previousRenderSlide.apply(this, arguments);
            }

            if (this._renderSlideRunning) {
                return Promise.resolve();
            }

            this._renderSlideRunning = true;
            try {
                var $content = this.$('.o_wslides_fs_content');
                $content.empty();

                if (this.websiteAnimateWidget) {
                    this.websiteAnimateWidget.destroy();
                    this.websiteAnimateWidget = null;
                }

                if (slide.category === 'quiz' || slide.isQuiz) {
                    $content.addClass('bg-white');
                    var quizWidget = new Quiz(this, slide, this.channel);
                    return await quizWidget.appendTo($content);
                }

                if (slide.category === 'certification') {
                    await this._renderCertificationSlide($content, slide);
                } else if (_.contains(['document', 'infographic', 'local_external', 'bunny', 'scorm'], slide.category)) {
                    $content.html(QWeb.render('website.slides.fullscreen.content', {widget: this}));
                } else if (slide.category === 'video' && slide.videoSourceType === 'google_drive') {
                    $content.html(QWeb.render('website.slides.fullscreen.video.google_drive', {widget: this}));
                } else if (slide.category === 'article') {
                    await this._renderArticleSlide($content, slide);
                }

                unhideConditionalElements();
            } finally {
                this._renderSlideRunning = false;
            }
        },

        _renderCertificationSlide: async function ($content, slide) {
            try {
                var slideData = await this._rpc({
                    route: '/slides/slide/get_slide_data_description',
                    params: {slide_id: slide.id},
                });

                slide.slide_description = slideData.slide_description || '';
                slide.survey_description = this._sanitizeHtmlContent ?
                    this._sanitizeHtmlContent(slideData.survey_description || '') :
                    (slideData.survey_description || '');
                slide.use_html_embed = slideData.use_html_embed;
            } catch (error) {
                console.error('Error fetching slide data:', error);
                slide.slide_description = _t('Description not available');
                slide.survey_description = _t('Content not available');
                slide.use_html_embed = false;
            }

            $content.html(QWeb.render('website.slides.fullscreen.certification', {
                widget: this,
                slide: slide,
                slide_description: slide.slide_description,
                survey_description: slide.survey_description,
                use_html_embed: slide.use_html_embed,
            }));

            if (this._adjustIframeHeight) {
                this._adjustIframeHeight();
            }
        },

        _renderArticleSlide: async function ($content, slide) {
            try {
                var slideData = await this._rpc({
                    route: '/slides/slide/get_slide_data_custom',
                    params: {slide_id: slide.id},
                });
                slide.msn_custom = slideData.msn_custom || false;
            } catch (error) {
                console.error('Error fetching custom article slide data:', error);
                slide.msn_custom = false;
            }

            if (slide.msn_custom) {
                var customTemplateHtml = QWeb.render('custom_html_template', {slide: slide});
                $content.empty().append(
                    '<div class="o_wslide_fs_article_content bg-white block w-100 overflow-auto p-3">' +
                    customTemplateHtml +
                    (slide.htmlContent || '') +
                    '</div>'
                );
            } else {
                this.websiteAnimateWidget = new publicWidget.registry.WebsiteAnimate();
                var $wpContainer = $('<div>')
                    .addClass('o_wslide_fs_article_content bg-white block w-100 overflow-auto p-3');
                $wpContainer.html(slide.htmlContent || '');
                $content.empty().append($wpContainer);
                this.trigger_up('widgets_start_request', {$target: $content});
                this.websiteAnimateWidget.attachTo($wpContainer);
            }
        },
    });
});