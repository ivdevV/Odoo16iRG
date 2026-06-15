odoo.define('irg_elearning_url_slide.fullscreen_url', function (require) {
    'use strict';

    const core = require('web.core');
    const QWeb = core.qweb;
    const Fullscreen = require('@website_slides/js/slides_course_fullscreen_player')[Symbol.for('default')];

    Fullscreen.include({
        xmlDependencies: (Fullscreen.prototype.xmlDependencies || []).concat([
            '/irg_elearning_url_slide/static/src/xml/website_slides_fullscreen_url.xml',
        ]),

        _preprocessSlideData: function (slidesDataList) {
            const res = this._super.apply(this, arguments);

            slidesDataList.forEach(function (slideData) {
                if (slideData.category === 'url') {
                    slideData.hasQuestion = !!slideData.hasQuestion;
                    if (!slideData.hasQuestion) {
                        slideData._autoSetDone = true;
                    }
                }
            });

            return res;
        },

        _renderSlide: function () {
            const def = this._super.apply(this, arguments);
            const $content = this.$('.o_wslides_fs_content');
            const slide = this.get('slide');

            if (slide.category === 'url') {
                $content.html(QWeb.render('website.slides.fullscreen.content', {widget: this}));
            }

            return Promise.all([def]);
        },
    });
});
