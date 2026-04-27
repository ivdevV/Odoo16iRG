/** @odoo-module **/

/**
 * irg_html_embed_slide — embed_fullscreen.js
 *
 * Extensión del reproductor en pantalla completa (Fullscreen).
 * Cuando el slide tiene irg_use_html_embed activo, obtiene el HTML
 * vía RPC y lo renderiza en un iframe con auto-altura en lugar del
 * contenido nativo de Odoo.
 *
 * CORRECCIÓN CLAVE respecto a isep_content_interactive:
 *   _fetchEmbedContent() se llama SIEMPRE al inicio de _renderSlide(),
 *   antes de decidir qué rama renderizar.
 */

import Fullscreen from '@website_slides/js/slides_course_fullscreen_player';

const IFRAME_SANDBOX = [
    'allow-scripts',
    'allow-same-origin',
    'allow-forms',
    'allow-popups',
    'allow-modals',
    'allow-downloads',
    'allow-popups-to-escape-sandbox',
    'allow-top-navigation-by-user-activation',
].join(' ');

function buildSrcdoc(html) {
    return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>html,body{margin:0;padding:0} body{overflow:hidden}</style>
<script>
(function(){
  var scheduled=false;
  function postHeight(){
    scheduled=false;
    var h=Math.max(
      document.documentElement.scrollHeight||0,
      document.body.scrollHeight||0,
      document.documentElement.offsetHeight||0,
      document.body.offsetHeight||0,
      document.documentElement.clientHeight||0
    );
    window.parent.postMessage({__irg_embed__:true,height:h},'*');
  }
  function schedule(){ if(!scheduled){scheduled=true;requestAnimationFrame(postHeight);} }
  window.addEventListener('load',schedule);
  window.addEventListener('resize',schedule);
  document.addEventListener('DOMContentLoaded',schedule);
  new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true,attributes:true,characterData:true});
  if('ResizeObserver'in window){new ResizeObserver(schedule).observe(document.documentElement);}
  setTimeout(schedule,50);setTimeout(schedule,250);setTimeout(schedule,1000);

  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a[href]');
    if(!a) return;
    var href=a.getAttribute('href')||'';
    var isDownload=a.hasAttribute('download')
      ||/\\/web\\/content\\//.test(href)
      ||a.getAttribute('data-download')==='1';
    if(isDownload){
      e.preventDefault();
      var u=new URL(href,window.location.href).toString();
      window.parent.postMessage({__irg_embed_download__:u},'*');
    }
  },true);

  window.addEventListener('message',function(ev){
    var d=ev&&ev.data||{};
    if(d.__irg_embed_getHeight__) schedule();
    if(d.__irg_embed_forwardResize__){dispatchEvent(new Event('resize'));schedule();}
  });
})();
<\/script>
</head>
<body>${html}</body>
</html>`;
}

Fullscreen.include({

    // -----------------------------------------------------------------------
    // Inicialización del estado interno
    // -----------------------------------------------------------------------
    init() {
        this._super(...arguments);
        this._irgIframe = null;
        this._irgMsgHandler = null;
        this._irgResizeHandler = null;
        this._irgScrollTargets = [];
    },

    // -----------------------------------------------------------------------
    // Obtiene el HTML embebido del servidor.
    // Devuelve { is_embed: bool, html_content: string }
    // -----------------------------------------------------------------------
    async _fetchEmbedContent() {
        const slide = this.get('slide');
        let result = { is_embed: false, html_content: '' };
        try {
            const r = await this._rpc({
                route: '/irg/slide/get_embed_content',
                params: { slide_id: slide.id },
            });
            result = r || result;
        } catch (e) {
            console.error('[irg_html_embed_slide] Error fetching embed content', e);
        }
        slide.irg_use_html_embed = !!result.is_embed;
        slide.irgHtmlContent = result.html_content || '';
    },

    // -----------------------------------------------------------------------
    // Override del renderizado del slide
    // -----------------------------------------------------------------------
    async _renderSlide() {
        // IMPORTANTE: capturar _super ANTES de cualquier await,
        // ya que Odoo limpia la referencia al salir del contexto síncrono.
        const superRender = this._super.bind(this);

        const slide = this.get('slide');
        const $content = this.$('.o_wslides_fs_content');

        // Siempre consultamos el servidor antes de decidir qué renderizar
        await this._fetchEmbedContent();

        if (!slide.irg_use_html_embed) {
            // Sin embed: limpiar handlers y delegar al comportamiento nativo
            this._teardownIrgHandlers();
            return await superRender(...arguments);
        }

        // Con embed: construir iframe seguro
        $content.empty();

        const wrapper = document.createElement('div');
        wrapper.className = 'o_wslide_fs_article_content bg-white block w-100 overflow-auto p-3';
        wrapper.style.maxHeight = '100vh';

        const iframe = document.createElement('iframe');
        iframe.title = 'Contenido embebido';
        iframe.setAttribute('scrolling', 'no');
        iframe.setAttribute('allow', 'microphone; camera');
        iframe.setAttribute('sandbox', IFRAME_SANDBOX);
        iframe.style.cssText = 'border:none;width:100%;display:block;overflow:hidden;';
        iframe.setAttribute('srcdoc', buildSrcdoc(slide.irgHtmlContent));

        this._irgIframe = iframe;

        // ---- Handlers de mensaje (altura + descargas) ----
        this._irgMsgHandler = (event) => {
            if (event.source !== this._irgIframe?.contentWindow) return;
            const data = event.data || {};
            if (data.__irg_embed__ && typeof data.height === 'number' && data.height > 0) {
                this._irgIframe.style.height = data.height + 'px';
            }
            if (data.__irg_embed_download__) {
                this._irgTriggerDownload(data.__irg_embed_download__);
            }
        };
        window.addEventListener('message', this._irgMsgHandler);

        // ---- Handler de resize ----
        this._irgResizeHandler = () => {
            try { this._irgIframe?.contentWindow?.postMessage({ __irg_embed_forwardResize__: true }, '*'); } catch(_){}
        };
        window.addEventListener('resize', this._irgResizeHandler);
        this._irgScrollTargets.push([window, 'resize', this._irgResizeHandler]);

        iframe.addEventListener('load', () => {
            try { this._irgIframe?.contentWindow?.postMessage({ __irg_embed_getHeight__: true }, '*'); } catch(_){}
        });

        $content[0].appendChild(wrapper);
        wrapper.appendChild(iframe);
    },

    // -----------------------------------------------------------------------
    // Descarga segura desde el padre
    // -----------------------------------------------------------------------
    _irgTriggerDownload(url) {
        try {
            const u = new URL(url, window.location.href);
            const allowed = new Set([window.location.hostname, 'app.universidadisep.com']);
            if (!allowed.has(u.hostname)) return;
            const a = document.createElement('a');
            a.href = u.toString(); a.target = '_blank'; a.rel = 'noopener';
            document.body.appendChild(a); a.click(); a.remove();
        } catch(_){}
    },

    // -----------------------------------------------------------------------
    // Limpieza de event listeners al cambiar de slide o destruir
    // -----------------------------------------------------------------------
    _teardownIrgHandlers() {
        if (this._irgMsgHandler) {
            window.removeEventListener('message', this._irgMsgHandler);
            this._irgMsgHandler = null;
        }
        if (this._irgResizeHandler) {
            window.removeEventListener('resize', this._irgResizeHandler);
            this._irgResizeHandler = null;
        }
        for (const [target, evt, handler] of (this._irgScrollTargets || [])) {
            try { target.removeEventListener(evt, handler); } catch(_){}
        }
        this._irgScrollTargets = [];
        this._irgIframe = null;
    },

    destroy() {
        this._teardownIrgHandlers();
        this._super(...arguments);
    },
});
