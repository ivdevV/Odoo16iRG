/** @odoo-module **/

import Fullscreen from '@website_slides/js/slides_course_fullscreen_player';
import { _t } from 'web.core';

Fullscreen.include({
    init() {
        this._super(...arguments);
        this._fsIframe = null;
        this._onEmbedMessage = null;
        this._onParentScroll = null;
        this._onParentResize = null;
        this._scrollTargets = [];
    },

    async _fetchHtmlContent() {
        const slide = this.get('slide');
        const response = await this._rpc({
            route: '/slides/slide/get_html_content',
            params: { slide_id: slide.id },
        });
        slide.use_html_embed = !!(response && response.is_embed);
        slide.htmlContent = response && response.html_content;
    },

    async _renderSlide() {
        const renderSuper = this._super.bind(this);
        const renderArgs = arguments;
        const slide = this.get('slide');
        const $content = this.$('.o_wslides_fs_content');

        await this._fetchHtmlContent();

        if (!slide.use_html_embed) {
            this._teardownEmbedHandlers();
            return await renderSuper(...renderArgs);
        }

        $content.empty();

        const wrapper = document.createElement('div');
        wrapper.className = 'o_wslide_fs_article_content bg-white block w-100 overflow-auto p-3';
        wrapper.style.maxHeight = '100vh';

        const iframeId = 'slide_dynamic_iframe_' + Math.random().toString(36).slice(2);
        const iframe = document.createElement('iframe');
        iframe.id = iframeId;
        iframe.title = _t('Embedded content');
        iframe.setAttribute('scrolling', 'no');
        iframe.style.border = 'none';
        iframe.style.width = '100%';
        iframe.style.display = 'block';
        iframe.style.overflow = 'hidden';

        iframe.setAttribute('allow', 'microphone; camera');
        iframe.setAttribute('sandbox', [
            'allow-scripts',
            'allow-same-origin',
            'allow-forms',
            'allow-popups',
            'allow-modals',
            'allow-downloads',
            'allow-popups-to-escape-sandbox',
            'allow-top-navigation-by-user-activation',
        ].join(' '));

        iframe.setAttribute('srcdoc', `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>html,body{margin:0;padding:0} body{overflow:hidden}</style>
<script>
(function(){
  let scheduled=false;
  function postHeight(){scheduled=false; var h=Math.max(
    document.documentElement.scrollHeight||0,
    document.body.scrollHeight||0,
    document.documentElement.offsetHeight||0,
    document.body.offsetHeight||0,
    document.documentElement.clientHeight||0
  ); window.parent.postMessage({__oembed__:true,height:h},'*');}
  function schedule(){ if(!scheduled){scheduled=true; requestAnimationFrame(postHeight);} }
  addEventListener('load',schedule); addEventListener('resize',schedule); document.addEventListener('DOMContentLoaded',schedule);
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true,attributes:true,characterData:true});
  if('ResizeObserver'in window){ new ResizeObserver(schedule).observe(document.documentElement); }
  setTimeout(schedule,50); setTimeout(schedule,250); setTimeout(schedule,1000);

  document.addEventListener('click', function(e){
    const a = e.target.closest && e.target.closest('a[href]');
    if(!a) return;
    const href = a.getAttribute('href') || '';
    const isDownloadLike = a.hasAttribute('download')
      || /\/web\/content\//.test(href)
      || a.getAttribute('data-download') === '1';
    if(isDownloadLike){
      e.preventDefault();
      const u = new URL(href, window.location.href).toString();
      window.parent.postMessage({__oembed_download: u}, '*');
    }
  }, true);

  addEventListener('message', function(ev){
    var d = ev && ev.data || {};
    if(d.__oembed_getHeight) schedule();
    if(d.__oembed_forwardScroll) dispatchEvent(new Event('scroll'));
    if(d.__oembed_forwardResize){ dispatchEvent(new Event('resize')); schedule(); }
  });
})();
</script>
</head>
<body>${slide.htmlContent || ''}</body>
</html>`);

        this._fsIframe = iframe;

        iframe.addEventListener('load', () => {
            this._requestChildMeasure();
            this._forwardResize();
        });

        this._onEmbedMessage = (event) => {
            if (event.source !== this._fsIframe?.contentWindow) {
                return;
            }
            const data = event.data || {};
            if (data.__oembed__ && typeof data.height === 'number' && data.height > 0) {
                this._fsIframe.style.height = data.height + 'px';
            }
            if (data.__oembed_download) {
                this._triggerTopDownload(data.__oembed_download);
            }
        };
        window.addEventListener('message', this._onEmbedMessage);

        const fsContent = this.$('.o_wslides_fs_content')[0];
        const onParentScroll = () => this._forwardScroll();
        const onParentResize = () => {
            this._forwardResize();
            this._requestChildMeasure();
        };
        this._onParentScroll = onParentScroll;
        this._onParentResize = onParentResize;

        wrapper.addEventListener('scroll', this._onParentScroll, { passive: true });
        this._scrollTargets.push([wrapper, 'scroll', this._onParentScroll]);

        if (fsContent) {
            fsContent.addEventListener('scroll', this._onParentScroll, { passive: true });
            this._scrollTargets.push([fsContent, 'scroll', this._onParentScroll]);
        }

        window.addEventListener('scroll', this._onParentScroll, { passive: true });
        this._scrollTargets.push([window, 'scroll', this._onParentScroll]);

        window.addEventListener('resize', this._onParentResize);
        this._scrollTargets.push([window, 'resize', this._onParentResize]);

        $content[0].appendChild(wrapper);
        wrapper.appendChild(iframe);
    },

    _triggerTopDownload(url) {
        try {
            const downloadUrl = new URL(url, window.location.href);
            const allowedHosts = new Set([
                window.location.hostname,
                'app.universidadisep.com',
            ]);
            if (!allowedHosts.has(downloadUrl.hostname)) {
                return;
            }

            const link = document.createElement('a');
            link.href = downloadUrl.toString();
            link.target = '_blank';
            link.rel = 'noopener';
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {}
    },

    _requestChildMeasure() {
        try {
            this._fsIframe?.contentWindow?.postMessage({ __oembed_getHeight: true }, '*');
        } catch (error) {}
    },

    _forwardScroll() {
        try {
            this._fsIframe?.contentWindow?.postMessage({ __oembed_forwardScroll: true }, '*');
        } catch (error) {}
    },

    _forwardResize() {
        try {
            this._fsIframe?.contentWindow?.postMessage({ __oembed_forwardResize: true }, '*');
        } catch (error) {}
    },

    _teardownEmbedHandlers() {
        if (this._onEmbedMessage) {
            window.removeEventListener('message', this._onEmbedMessage);
            this._onEmbedMessage = null;
        }
        if (this._scrollTargets?.length) {
            for (const [target, eventName, handler] of this._scrollTargets) {
                try {
                    target.removeEventListener(eventName, handler);
                } catch (error) {}
            }
        }
        this._scrollTargets = [];
        this._fsIframe = null;
    },

    destroy() {
        this._teardownEmbedHandlers();
        this._super(...arguments);
    },
});