/** @odoo-module **/

import publicWidget from 'web.public.widget';

publicWidget.registry.SlideHTMLEmbed = publicWidget.Widget.extend({
    selector: '.o_html_embed_wrapper',
    start: function () {
        const html = this.el.dataset.embed;
        if (!html) return;

        const iframeId = 'slide_dynamic_iframe_' + Math.random().toString(36).slice(2);
        const iframe = document.createElement('iframe');
        iframe.id = iframeId;
        iframe.title = 'Contenido embebido';
        iframe.setAttribute('width', '100%');
        iframe.setAttribute('scrolling', 'no');
        iframe.style.border = 'none';
        iframe.style.width = '100%';
        iframe.style.display = 'block';
        iframe.style.overflow = 'hidden';

        // Permisos útiles
        iframe.setAttribute('allow', 'microphone; camera');
        iframe.setAttribute('sandbox', [
            'allow-scripts',
            'allow-same-origin',
            'allow-forms',
            'allow-popups',
            'allow-modals',
            'allow-downloads',
            'allow-popups-to-escape-sandbox',
            'allow-top-navigation-by-user-activation'
        ].join(' '));

        iframe.setAttribute('srcdoc', `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
  html,body{margin:0;padding:0} body{overflow:hidden}
</style>
<script>
(function(){
  // --- auto-altura ---
  let scheduled=false;
  function postHeight(){
    scheduled=false;
    var h=Math.max(
      document.documentElement.scrollHeight||0,
      document.body.scrollHeight||0,
      document.documentElement.offsetHeight||0,
      document.body.offsetHeight||0,
      document.documentElement.clientHeight||0
    );
    window.parent.postMessage({__oembed__:true,height:h},'*');
  }
  function schedule(){ if(!scheduled){scheduled=true; requestAnimationFrame(postHeight);} }
  window.addEventListener('load',schedule);
  window.addEventListener('resize',schedule);
  document.addEventListener('DOMContentLoaded',schedule);
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true,attributes:true,characterData:true});
  if('ResizeObserver'in window){ new ResizeObserver(schedule).observe(document.documentElement); }

  setTimeout(schedule,50); setTimeout(schedule,250); setTimeout(schedule,1000);

  // --- interceptar descargas: /web/content..., <a download>, data-download="1"
  document.addEventListener('click', function(e){
    const a = e.target.closest && e.target.closest('a[href]');
    if(!a) return;
    const href = a.getAttribute('href') || '';
    const isDownloadLike = a.hasAttribute('download')
      || /\\/web\\/content\\//.test(href)
      || a.getAttribute('data-download') === '1';

    if(isDownloadLike){
      e.preventDefault();
      // normaliza URL relativa a absoluta
      const u = new URL(href, window.location.href).toString();
      window.parent.postMessage({__oembed_download: u}, '*');
    }
  }, true);

  // re-medición on-demand
  window.addEventListener('message', function(ev){
    if(ev && ev.data && ev.data.__oembed_getHeight) schedule();
  });
})();
</script>
</head>
<body>${html}</body>
</html>`);

        const requestChildMeasure = () => {
            try { iframe.contentWindow && iframe.contentWindow.postMessage({ __oembed_getHeight: true }, '*'); } catch(e){}
        };

        iframe.addEventListener('load', requestChildMeasure);

        const onMessage = (event) => {
            if (event.source !== iframe.contentWindow) return;
            const data = event.data || {};
            if (data.__oembed__ && typeof data.height === 'number' && data.height > 0) {
                iframe.style.height = data.height + 'px';
            }
            if (data.__oembed_download) {
                this._triggerTopDownload(data.__oembed_download);
            }
        };
        window.addEventListener('message', onMessage);


        const onResize = () => requestChildMeasure();
        window.addEventListener('resize', onResize);

        this.el.appendChild(iframe);
        this._super.apply(this, arguments);
        this.on('destroy', this, () => {
            window.removeEventListener('message', onMessage);
            window.removeEventListener('resize', onResize);
        });
    },

    _triggerTopDownload(url) {
        try {
            const u = new URL(url, window.location.href);
            const allowedHosts = new Set([
                window.location.hostname,            // mismo host
                'app.universidadisep.com'            
            ]);
            if (!allowedHosts.has(u.hostname)) return; 

            const a = document.createElement('a');
            a.href = u.toString();
            a.target = '_blank'; // o '_self' si quieres en la misma pestaña
            a.rel = 'noopener';
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            // opcional: log
        }
    },
});
