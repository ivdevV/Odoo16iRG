odoo.define('irg_course_portal_tiles.help_chatbot', function(require){
    'use strict';
    var ajax = require('web.ajax');
    // Simple client-side chatbot widget: attach to #irg-help-chat if present
    document.addEventListener('DOMContentLoaded', function(){
        var container = document.getElementById('irg-help-chat');
        if(!container) { return; }
        var chatBox = document.createElement('div');
        chatBox.className = 'irg-chat-box p-3 border';
        chatBox.innerHTML = '\n            <div id="irg-chat-log" style="min-height:120px;max-height:300px;overflow:auto;margin-bottom:8px;"></div>\n            <div class="input-group">\n                <input id="irg-chat-input" class="form-control" placeholder="Pregúntame algo...">\n                <button id="irg-chat-send" class="btn btn-primary">Enviar</button>\n            </div>';
        container.appendChild(chatBox);
        var log = chatBox.querySelector('#irg-chat-log');
        var input = chatBox.querySelector('#irg-chat-input');
        var btn = chatBox.querySelector('#irg-chat-send');
        function appendMsg(who, text){
            var p = document.createElement('div');
            p.className = who==='user' ? 'text-end mb-1' : 'text-start mb-1';
            p.textContent = text;
            log.appendChild(p);
            log.scrollTop = log.scrollHeight;
        }
        btn.addEventListener('click', function(){
            var msg = input.value && input.value.trim();
            if(!msg) { return; }
            appendMsg('user', msg);
            input.value = '';
            ajax.jsonRpc('/help/chat', 'call', {message: msg}).then(function(res){
                appendMsg('bot', res.reply || 'Lo siento, no hay respuesta.');
            }).guardedCatch(function(){
                appendMsg('bot', 'Error de conexión al chatbot.');
            });
        });
    });
});
