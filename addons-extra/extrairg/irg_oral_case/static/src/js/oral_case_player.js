odoo.define('irg_oral_case.player', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var booted = new WeakSet();
    var CONSENT_FALLBACK = (
        'Texto provisional, pendiente de validación legal. ' +
        'Al continuar autorizas que se grabe tu imagen y tu voz para evaluar este caso clínico. ' +
        'La grabación se envía a un servicio de transcripción y de puntuación. ' +
        'La nota final la decide el profesor. ' +
        'Este texto todavía no ha sido revisado por el responsable de protección de datos.'
    );

    function boot(el) {
        if (!el || booted.has(el) || !el.classList || !el.classList.contains('o_irg_oral_case')) {
            return;
        }
        booted.add(el);
        var player = new OralCasePlayer(el);
        player.start();
    }

    function scan(root) {
        if (!root || !root.querySelectorAll) {
            return;
        }
        if (root.classList && root.classList.contains('o_irg_oral_case')) {
            boot(root);
        }
        var nodes = root.querySelectorAll('.o_irg_oral_case');
        for (var i = 0; i < nodes.length; i++) {
            boot(nodes[i]);
        }
    }

    function element(tag, className, text) {
        var node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        if (text) {
            node.textContent = text;
        }
        return node;
    }

    function isSafeHttps(url) {
        if (!url || /[\s\\]/.test(url)) {
            return false;
        }
        try {
            var parsed = new URL(url);
            return parsed.protocol === 'https:' && !parsed.username && !parsed.password && !!parsed.hostname;
        } catch (error) {
            return false;
        }
    }

    function isVimeoHost(url) {
        if (!isSafeHttps(url)) {
            return false;
        }
        var host = new URL(url).hostname;
        return host === 'vimeo.com' || host === 'player.vimeo.com';
    }

    function vimeoSrc(url) {
        var parsed = new URL(url);
        if (parsed.hostname === 'player.vimeo.com') {
            return parsed.toString();
        }
        var parts = parsed.pathname.split('/').filter(Boolean);
        var id = parts.length ? parts[parts.length - 1] : '';
        if (!/^[0-9]+$/.test(id)) {
            return null;
        }
        var target = new URL('https://player.vimeo.com/video/' + id);
        parsed.searchParams.forEach(function (value, key) {
            target.searchParams.set(key, value);
        });
        return target.toString();
    }

    function loadVimeoApi() {
        return new Promise(function (resolve, reject) {
            if (window.Vimeo && window.Vimeo.Player) {
                resolve();
                return;
            }
            var script = document.createElement('script');
            script.src = 'https://player.vimeo.com/api/player.js';
            script.onload = function () { resolve(); };
            script.onerror = function () { reject(new Error('vimeo')); };
            document.head.appendChild(script);
        });
    }

    function OralCasePlayer(root) {
        this.root = root;
        this.slideId = parseInt(root.getAttribute('data-slide-id'), 10);
        this.info = null;
        this.stream = null;
        this.takes = [];
        this.index = 0;
        this.blob = null;
        this.duration = 0;
        this.recorder = null;
        this.timer = null;
        this.startedAt = 0;
    }

    OralCasePlayer.prototype.start = function () {
        var self = this;
        this.root.textContent = '';
        if (!this.slideId) {
            this.showError('Falta el identificador del slide.');
            return;
        }
        fetch('/irg/oral_case/bootstrap?slide_id=' + this.slideId, {credentials: 'same-origin'})
            .then(function (response) { return response.json(); })
            .then(function (info) {
                if (!info || !info.ok) {
                    self.showError('No se ha podido abrir el caso.');
                    return;
                }
                self.info = info;
                self.renderConsent();
            })
            .catch(function () {
                self.showError('No se ha podido abrir el caso.');
            });
    };

    OralCasePlayer.prototype.showError = function (message) {
        var panel = element('div', 'o_irg_panel');
        panel.appendChild(element('p', 'o_irg_error', message));
        this.root.textContent = '';
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.renderConsent = function () {
        var self = this;
        this.root.textContent = '';
        var legal = element('div', 'o_irg_legal');
        if (this.info.consent_legal_status === 'pending_legal_review') {
            legal.appendChild(element('p', null, 'Texto provisional, pendiente de validación legal.'));
        }
        legal.appendChild(element('p', null, this.info.consent_text || CONSENT_FALLBACK));
        var box = element('label');
        var input = document.createElement('input');
        input.type = 'checkbox';
        box.appendChild(input);
        box.appendChild(document.createTextNode(' He leído el texto y acepto que se active la cámara.'));
        legal.appendChild(box);
        var actions = element('div', 'o_irg_actions');
        var button = element('button', null, 'Aceptar y activar la cámara');
        button.type = 'button';
        button.addEventListener('click', function () {
            if (!input.checked) {
                self.showError('Marca la casilla de consentimiento para continuar.');
                return;
            }
            self.askCamera();
        });
        actions.appendChild(button);
        legal.appendChild(actions);
        this.root.appendChild(legal);
    };

    OralCasePlayer.prototype.askCamera = function () {
        var self = this;
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showError('Este navegador no puede usar la cámara.');
            return;
        }
        navigator.mediaDevices.getUserMedia({video: true, audio: true}).then(function (stream) {
            self.stream = stream;
            self.index = 0;
            self.takes = [];
            self.playCurrent();
        }).catch(function () {
            self.showError('No se ha podido usar la cámara. Sin ese permiso no se puede continuar.');
        });
    };

    OralCasePlayer.prototype.segments = function () {
        if (this.info.mode === 'clips') {
            return this.info.segments || [];
        }
        return [{
            index: 1,
            id: 0,
            name: 'Intervención',
            prompt: 'Graba tu intervención.',
            clip_url: '',
            max_seconds: this.info.max_duration_seconds,
            allow_retry: true,
            listen_clip_url: '',
        }];
    };

    OralCasePlayer.prototype.playCurrent = function () {
        var segment = this.segments()[this.index];
        if (!segment) {
            this.submitAll();
            return;
        }
        this.blob = null;
        this.root.textContent = '';
        var panel = element('div', 'o_irg_panel');
        panel.appendChild(element('h3', null, segment.name || ('Tramo ' + segment.index)));
        this.root.appendChild(panel);
        if (segment.clip_url) {
            this.mountClip(panel, segment.clip_url, false, function () {
                this.renderPrompt(segment);
            }.bind(this));
        } else {
            this.renderPrompt(segment);
        }
    };

    OralCasePlayer.prototype.mountClip = function (panel, url, loop, onEnded) {
        if (!isSafeHttps(url)) {
            this.showError('La URL del clip no es válida.');
            return;
        }
        if (isVimeoHost(url)) {
            var src = vimeoSrc(url);
            if (!src) {
                this.showError('La URL de Vimeo no es válida.');
                return;
            }
            var frame = document.createElement('iframe');
            frame.setAttribute('allow', 'autoplay; fullscreen');
            frame.src = src;
            panel.appendChild(frame);
            if (loop) {
                return;
            }
            loadVimeoApi().then(function () {
                var player = new window.Vimeo.Player(frame);
                player.on('ended', onEnded);
            }).catch(function () {
                this.showError('No se ha podido cargar el reproductor de Vimeo.');
            }.bind(this));
            return;
        }
        var video = document.createElement('video');
        video.controls = !loop;
        video.playsInline = true;
        video.loop = !!loop;
        video.muted = !!loop;
        video.src = url;
        panel.appendChild(video);
        if (loop) {
            video.play().catch(function () {});
            return video;
        }
        video.addEventListener('ended', onEnded);
        video.play().catch(function () {});
        return video;
    };

    OralCasePlayer.prototype.renderPrompt = function (segment) {
        var self = this;
        var panel = element('div', 'o_irg_panel');
        panel.appendChild(element('p', null, segment.prompt || ''));
        var timer = element('p', 'o_irg_timer', this.formatTime(segment.max_seconds));
        panel.appendChild(timer);
        var preview = document.createElement('video');
        preview.autoplay = true;
        preview.muted = true;
        preview.playsInline = true;
        if (this.stream) {
            preview.srcObject = this.stream;
        }
        panel.appendChild(preview);
        var listenUrl = segment.listen_clip_url || '';
        if (listenUrl && isSafeHttps(listenUrl) && !isVimeoHost(listenUrl)) {
            this.mountClip(panel, listenUrl, true);
        }
        var actions = element('div', 'o_irg_actions');
        var record = element('button', null, 'Grabar');
        record.type = 'button';
        var stop = element('button', 'o_irg_secondary', 'Parar');
        stop.type = 'button';
        stop.disabled = true;
        record.addEventListener('click', function () {
            record.disabled = true;
            stop.disabled = false;
            self.record(segment, timer, function () {
                stop.disabled = true;
                self.afterTake(segment, actions);
            });
        });
        stop.addEventListener('click', function () {
            self.stopRecorder();
        });
        actions.appendChild(record);
        actions.appendChild(stop);
        panel.appendChild(actions);
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.record = function (segment, timer, done) {
        var self = this;
        var chunks = [];
        var options = {};
        if (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('video/webm')) {
            options.mimeType = 'video/webm';
        }
        this.recorder = new MediaRecorder(this.stream, options);
        this.startedAt = Date.now();
        this.recorder.ondataavailable = function (event) {
            if (event.data && event.data.size) {
                chunks.push(event.data);
            }
        };
        this.recorder.onstop = function () {
            self.duration = Math.round((Date.now() - self.startedAt) / 1000);
            self.blob = new Blob(chunks, {type: 'video/webm'});
            if (self.timer) {
                clearInterval(self.timer);
            }
            done();
        };
        this.recorder.start();
        var left = segment.max_seconds || this.info.max_duration_seconds;
        this.timer = setInterval(function () {
            left -= 1;
            timer.textContent = self.formatTime(Math.max(left, 0));
            if (left <= 0) {
                self.stopRecorder();
            }
        }, 1000);
    };

    OralCasePlayer.prototype.stopRecorder = function () {
        if (this.recorder && this.recorder.state === 'recording') {
            this.recorder.stop();
        }
    };

    OralCasePlayer.prototype.afterTake = function (segment, actions) {
        var self = this;
        var next = element('button', null, 'Continuar');
        next.type = 'button';
        next.addEventListener('click', function () {
            self.takes.push({
                index: segment.index,
                id: segment.id,
                blob: self.blob,
                duration: self.duration,
            });
            self.index += 1;
            self.playCurrent();
        });
        actions.appendChild(next);
        if (segment.allow_retry) {
            var retry = element('button', 'o_irg_secondary', 'Repetir toma');
            retry.type = 'button';
            retry.addEventListener('click', function () {
                self.playCurrent();
            });
            actions.appendChild(retry);
        }
    };

    OralCasePlayer.prototype.submitAll = function () {
        var self = this;
        this.stopStream();
        var panel = element('div', 'o_irg_panel');
        panel.appendChild(element('p', null, 'Enviando la intervención…'));
        this.root.textContent = '';
        this.root.appendChild(panel);
        var body = new FormData();
        body.append('csrf_token', this.info.csrf_token);
        body.append('slide_id', String(this.info.slide_id));
        body.append('consent_date', new Date().toISOString().slice(0, 10));
        body.append('autoevaluacion_json', JSON.stringify({
            origen: 'reproductor',
            tramos: this.takes.length,
        }));
        if (this.info.mode === 'clips') {
            body.append('clips_json', JSON.stringify(this.takes.map(function (take) {
                return {
                    index: take.index,
                    segment_id: take.id,
                    duration_seconds: take.duration,
                };
            })));
            this.takes.forEach(function (take) {
                body.append('clip_' + take.index, take.blob, 'clip-' + take.index + '.webm');
            });
        } else if (this.takes[0]) {
            body.append('duracion_seg', String(this.takes[0].duration));
            body.append('video', this.takes[0].blob, 'caso.webm');
        }
        fetch(this.info.submit_url, {method: 'POST', body: body, credentials: 'same-origin'})
            .then(function (response) { return response.json(); })
            .then(function (payload) {
                panel.textContent = '';
                if (!payload || !payload.ok) {
                    panel.appendChild(element('p', 'o_irg_error', 'No se ha podido enviar la intervención.'));
                    return;
                }
                panel.appendChild(element('p', null, 'Intervención enviada. La nota final la pondrá el profesor.'));
            })
            .catch(function () {
                panel.textContent = '';
                panel.appendChild(element('p', 'o_irg_error', 'No se ha podido enviar la intervención.'));
            });
    };

    OralCasePlayer.prototype.stopStream = function () {
        if (!this.stream) {
            return;
        }
        this.stream.getTracks().forEach(function (track) { track.stop(); });
        this.stream = null;
    };

    OralCasePlayer.prototype.formatTime = function (seconds) {
        var value = Math.max(0, parseInt(seconds, 10) || 0);
        var minutes = Math.floor(value / 60);
        var rest = value % 60;
        return String(minutes) + ':' + (rest < 10 ? '0' : '') + String(rest);
    };

    publicWidget.registry.IrgOralCasePlayer = publicWidget.Widget.extend({
        selector: '.o_irg_oral_case',
        start: function () {
            boot(this.el);
            return this._super.apply(this, arguments);
        },
    });

    if (document.body) {
        scan(document.body);
        var observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                for (var i = 0; i < mutation.addedNodes.length; i++) {
                    scan(mutation.addedNodes[i]);
                }
            });
        });
        observer.observe(document.body, {childList: true, subtree: true});
    }

    return {isSafeHttps: isSafeHttps, isVimeoHost: isVimeoHost, vimeoSrc: vimeoSrc};
});
