(function () {
    'use strict';

    function initN8nChat() {
        // Evitar inicializar múltiples veces en la misma vista/página
        if (window.n8nChatInitialized) {
            return;
        }

        const configEl = document.getElementById('irg_n8n_chat_bubble_config');
        if (!configEl) {
            return;
        }

        const webhookUrl = configEl.getAttribute('data-webhook-url');
        if (!webhookUrl) {
            return;
        }

        const title = configEl.getAttribute('data-title') || 'Soporte Académico';
        const welcomeMsg = configEl.getAttribute('data-welcome-msg') || '¡Hola! ¿En qué te puedo ayudar hoy?';
        const studentName = configEl.getAttribute('data-student-name') || '';
        const studentEmail = configEl.getAttribute('data-student-email') || '';
        const courseName = configEl.getAttribute('data-course-name') || '';
        const subjectName = configEl.getAttribute('data-subject-name') || '';

        // Marcar como inicializado para prevenir colisiones o bucles de llamadas
        window.n8nChatInitialized = true;
        setupFullscreenObserver();

        // Cargar el CSS del widget de chat de n8n si no existe
        if (!document.getElementById('n8n-chat-style')) {
            const link = document.createElement('link');
            link.id = 'n8n-chat-style';
            link.rel = 'stylesheet';
            link.href = 'https://cdn.jsdelivr.net/npm/@n8n/chat/dist/style.css';
            document.head.appendChild(link);
        }

        // Cargar el bundle ES del chat de n8n dinámicamente
        const customWelcome = '¡Hola! Soy tu tutor virtual, pregúntame cualquier cosa 🤖';
        import('https://cdn.jsdelivr.net/npm/@n8n/chat/dist/chat.bundle.es.js')
            .then(function (module) {
                module.createChat({
                    webhookUrl: webhookUrl,
                    showWelcomeScreen: true,
                    defaultLanguage: 'es',
                    initialMessages: [customWelcome],
                    i18n: {
                        es: {
                            title: title,
                            subtitle: customWelcome,
                            getStarted: 'Iniciar chat',
                            inputPlaceholder: 'Escribe tu consulta...'
                        },
                        en: {
                            title: title,
                            subtitle: 'Hi! I am your virtual tutor, ask me anything 🤖',
                            getStarted: 'Start chat',
                            inputPlaceholder: 'Type your question...'
                        }
                    },
                    metadata: {
                        studentName: studentName,
                        studentEmail: studentEmail,
                        courseName: courseName,
                        subjectName: subjectName
                    }
                });
            })
            .catch(function (err) {
                console.error('Error al instanciar el chat de n8n:', err);
                window.n8nChatInitialized = false;
            });
    }

    function injectFullscreenButton(header) {
        if (header.querySelector('.n8n-chat-fullscreen-btn')) {
            return;
        }

        const btn = document.createElement('button');
        btn.className = 'n8n-chat-fullscreen-btn';
        btn.type = 'button';
        btn.title = 'Pantalla completa';
        btn.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path class="fs-icon-enter" d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
        </svg>`;
        
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isFullscreen = document.body.classList.toggle('n8n-chat-fullscreen');
            btn.title = isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa';
            
            const path = btn.querySelector('path');
            if (isFullscreen) {
                // Exit fullscreen icon: shrink
                path.setAttribute('d', 'M4 14h6v6m10-6h-6v6M4 10h6V4m10 6h-6V4');
            } else {
                // Enter fullscreen icon: expand
                path.setAttribute('d', 'M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3');
            }
        });

        const closeBtn = header.querySelector('.chat-close-button');
        if (closeBtn) {
            header.insertBefore(btn, closeBtn);
        } else {
            header.appendChild(btn);
        }
    }

    function setupFullscreenObserver() {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === 1) {
                        const header = node.classList.contains('chat-header') 
                            ? node 
                            : node.querySelector('.chat-header');
                        if (header) {
                            injectFullscreenButton(header);
                        }
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });

        const header = document.querySelector('.chat-header');
        if (header) {
            injectFullscreenButton(header);
        }
    }

    // Registrar observadores o listeners de carga
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        initN8nChat();
    } else {
        document.addEventListener('DOMContentLoaded', initN8nChat);
    }
})();
