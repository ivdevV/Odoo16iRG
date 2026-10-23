odoo.define('irg_oral_case.player', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var logic = globalThis.IrgOralCaseLogic;
    var booted = new WeakSet();
    var hookedFrames = new WeakSet();
    var CONSENT_FALLBACK = (
        'Texto provisional, pendiente de validación legal. ' +
        'Al continuar autorizas que se grabe tu imagen y tu voz para evaluar este caso clínico. ' +
        'La grabación se envía a un servicio de transcripción y de puntuación. ' +
        'La nota final la decide el profesor. ' +
        'Este texto todavía no ha sido revisado por el responsable de protección de datos.'
    );
    var LOAD_ERROR = 'El vídeo no se ha podido cargar. Puedes leer la transcripción y responder igualmente.';
    var STALL_ERROR = 'El vídeo no ha terminado. Puedes leer la transcripción y responder igualmente.';

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
        if (root.tagName === 'IFRAME') {
            watchFrame(root);
        }
        if (root.classList && root.classList.contains('o_irg_oral_case')) {
            boot(root);
        }
        var nodes = root.querySelectorAll('.o_irg_oral_case');
        for (var i = 0; i < nodes.length; i++) {
            boot(nodes[i]);
        }
        var frames = root.querySelectorAll('iframe');
        for (var j = 0; j < frames.length; j++) {
            watchFrame(frames[j]);
        }
    }

    function ensureStyles(doc) {
        if (!doc || !doc.head || doc.getElementById('o_irg_oral_case_css')) {
            return;
        }
        if (doc.defaultView === window) {
            return;
        }
        var link = doc.createElement('link');
        link.id = 'o_irg_oral_case_css';
        link.rel = 'stylesheet';
        link.href = '/irg_oral_case/static/src/css/oral_case_player.css';
        doc.head.appendChild(link);
    }

    function scanFrame(iframe) {
        var doc = null;
        try {
            doc = iframe.contentDocument;
        } catch (error) {
            doc = null;
        }
        if (!doc || !doc.body) {
            return;
        }
        ensureStyles(doc);
        scan(doc.body);
    }

    function watchFrame(iframe) {
        if (!iframe || iframe.tagName !== 'IFRAME' || hookedFrames.has(iframe)) {
            return;
        }
        hookedFrames.add(iframe);
        iframe.addEventListener('load', function () {
            scanFrame(iframe);
        });
        scanFrame(iframe);
    }

    function element(doc, tag, className, text) {
        var node = doc.createElement(tag);
        if (className) {
            node.className = className;
        }
        if (text) {
            node.textContent = text;
        }
        return node;
    }

    function button(doc, className, text) {
        var node = element(doc, 'button', className, text);
        node.type = 'button';
        return node;
    }

    function loadVimeoApi(win, doc) {
        return new Promise(function (resolve, reject) {
            if (win.Vimeo && win.Vimeo.Player) {
                resolve();
                return;
            }
            var script = doc.createElement('script');
            script.src = 'https://player.vimeo.com/api/player.js';
            script.onload = function () { resolve(); };
            script.onerror = function () { reject(new Error('vimeo')); };
            (doc.head || doc.body).appendChild(script);
        });
    }

    function OralCasePlayer(root) {
        this.root = root;
        this.doc = root.ownerDocument;
        this.win = this.doc.defaultView || window;
        this.slideId = parseInt(root.getAttribute('data-slide-id'), 10);
        this.info = null;
        this.stream = null;
        this.takes = [];
        this.index = 0;
        this.blob = null;
        this.ext = 'webm';
        this.duration = 0;
        this.recorder = null;
        this.timer = null;
        this.watchTimer = null;
        this.pollTimer = null;
        this.startedAt = 0;
        this.audioPeak = -1;
        this.audioContext = null;
        this.analyser = null;
        this.meterOn = false;
        this.dirty = false;
        this.objectUrl = null;
        this.vimeoPlayer = null;
        this.vimeoReady = null;
        this.onLeave = null;
        var self = this;
        this.win.addEventListener('beforeunload', function (event) {
            if (!self.dirty) {
                return;
            }
            event.preventDefault();
            event.returnValue = '';
        });
    }

    OralCasePlayer.prototype.start = function () {
        var self = this;
        this.renderShell('Abriendo la actividad…', 'Abriendo la actividad…');
        if (!logic) {
            this.showMessage('No se ha podido abrir la actividad.', true);
            return;
        }
        if (!this.slideId) {
            this.showMessage('Esta actividad no está disponible ahora mismo. Avisa a tu profesorado.', true);
            return;
        }
        this.win.fetch('/irg/oral_case/bootstrap?slide_id=' + this.slideId, {credentials: 'same-origin'})
            .then(function (response) { return readPayload(response); })
            .then(function (info) {
                if (!info || !info.ok) {
                    self.showMessage(logic.errorMessage(info && info.error), true);
                    return;
                }
                self.info = info;
                self.showIntro();
            })
            .catch(function () {
                self.showMessage('No se ha podido abrir la actividad.', true);
            });
    };

    OralCasePlayer.prototype.segments = function () {
        if (this.info && this.info.mode === 'clips') {
            return this.info.segments || [];
        }
        return [{
            index: 1,
            id: 0,
            name: 'Intervención',
            student_text: 'Graba tu intervención en voz alta.',
            student_quote: '',
            transcript: '',
            clip_url: '',
            max_seconds: this.info ? this.info.max_duration_seconds : 90,
            allow_retry: true,
            listen_clip_url: (this.info && this.info.listen_clip_url) || '',
        }];
    };

    OralCasePlayer.prototype.renderShell = function (title, liveText) {
        this.clearTimers();
        this.meterOn = false;
        this.revokeTake();
        if (this.onLeave) {
            this.onLeave();
            this.onLeave = null;
        }
        this.root.textContent = '';
        var live = element(this.doc, 'div', 'o_irg_live');
        live.setAttribute('aria-live', 'polite');
        live.setAttribute('aria-atomic', 'true');
        this.live = live;
        this.root.appendChild(live);
        var heading = element(this.doc, 'h2', null, title);
        heading.tabIndex = -1;
        this.root.appendChild(heading);
        if (liveText) {
            live.textContent = liveText;
        }
        var self = this;
        this.win.setTimeout(function () {
            try {
                heading.focus();
            } catch (error) {
                return;
            }
        }, 0);
        return heading;
    };

    OralCasePlayer.prototype.setLive = function (text) {
        if (this.live && text) {
            this.live.textContent = text;
        }
    };

    OralCasePlayer.prototype.showMessage = function (message, isError) {
        this.renderShell(isError ? 'No se puede continuar' : 'Caso práctico oral', message);
        var panel = element(this.doc, 'div', 'o_irg_panel');
        panel.appendChild(element(this.doc, 'p', isError ? 'o_irg_error' : null, message));
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.showIntro = function () {
        var self = this;
        var total = this.segments().length;
        var limit = this.segments()[0] ? this.segments()[0].max_seconds : 90;
        var title = this.info.case_title || 'Caso práctico oral';
        this.renderShell(title, title);
        var panel = element(this.doc, 'div', 'o_irg_panel');
        if (this.info.mode === 'clips') {
            panel.appendChild(element(
                this.doc,
                'p',
                null,
                'Verás ' + total + ' fragmentos. Al final de cada uno, responde en voz alta como lo harías en consulta (hasta ' + limit + ' segundos). Puedes repetir cada respuesta antes de seguir.'
            ));
        } else {
            panel.appendChild(element(
                this.doc,
                'p',
                null,
                'Graba tu intervención en voz alta (hasta ' + limit + ' segundos). Puedes repetirla antes de enviarla.'
            ));
        }
        panel.appendChild(element(this.doc, 'p', 'o_irg_note', 'Busca un lugar tranquilo y ponte auriculares.'));
        var actions = element(this.doc, 'div', 'o_irg_actions');
        var start = button(this.doc, null, 'Empezar');
        start.addEventListener('click', function () { self.showConsent(); });
        actions.appendChild(start);
        panel.appendChild(actions);
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.showConsent = function () {
        var self = this;
        this.renderShell('Consentimiento', 'Consentimiento');
        var legal = element(this.doc, 'div', 'o_irg_legal');
        if (this.info.consent_legal_status === 'pending_legal_review') {
            legal.appendChild(element(this.doc, 'p', 'o_irg_kicker', 'Texto provisional, pendiente de validación legal.'));
        }
        legal.appendChild(element(this.doc, 'p', null, this.info.consent_text || CONSENT_FALLBACK));
        var box = element(this.doc, 'label');
        var input = this.doc.createElement('input');
        input.type = 'checkbox';
        box.appendChild(input);
        box.appendChild(this.doc.createTextNode('He leído la información y acepto que se grabe mi voz y mi imagen para esta actividad.'));
        legal.appendChild(box);
        var hint = element(this.doc, 'p', 'o_irg_error', '');
        hint.hidden = true;
        legal.appendChild(hint);
        var actions = element(this.doc, 'div', 'o_irg_actions');
        var accept = button(this.doc, null, 'Aceptar y continuar');
        accept.disabled = true;
        input.addEventListener('change', function () {
            accept.disabled = !input.checked;
            hint.hidden = true;
        });
        accept.addEventListener('click', function () {
            if (!input.checked) {
                hint.hidden = false;
                hint.textContent = 'Para continuar, marca la casilla de consentimiento.';
                self.setLive(hint.textContent);
                return;
            }
            self.showPermission();
        });
        actions.appendChild(accept);
        legal.appendChild(actions);
        this.root.appendChild(legal);
    };

    OralCasePlayer.prototype.showPermission = function () {
        var self = this;
        this.renderShell('Cámara y micrófono', 'Tu navegador te pedirá permiso para usar la cámara y el micrófono.');
        var panel = element(this.doc, 'div', 'o_irg_panel');
        panel.appendChild(element(this.doc, 'p', null, 'Tu navegador te pedirá permiso para usar la cámara y el micrófono. Pulsa «Permitir».'));
        var actions = element(this.doc, 'div', 'o_irg_actions');
        var go = button(this.doc, null, 'Continuar');
        go.addEventListener('click', function () { self.askCamera(); });
        actions.appendChild(go);
        panel.appendChild(actions);
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.askCamera = function () {
        var self = this;
        var media = this.win.navigator.mediaDevices;
        if (!media || !media.getUserMedia || !this.win.MediaRecorder) {
            this.showMessage('Tu navegador no permite grabar. Abre esta actividad en Chrome, Edge o Firefox actualizados.', true);
            return;
        }
        this.openStream({video: true, audio: true}).then(function () {
            self.showCameraCheck();
        }).catch(function (error) {
            self.showCameraError(error);
        });
    };

    OralCasePlayer.prototype.openStream = function (constraints) {
        var self = this;
        this.stopStream();
        return this.win.navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
            self.stream = stream;
            self.audioPeak = -1;
            return stream;
        });
    };

    OralCasePlayer.prototype.showCameraError = function (error) {
        var self = this;
        var name = error && error.name;
        var message = 'No se ha podido usar la cámara. Sin ese permiso no se puede continuar.';
        if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
            message = 'No tenemos permiso para usar la cámara o el micrófono. Actívalo en el icono del candado de la barra de direcciones y pulsa «Intentar de nuevo».';
        } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
            message = 'No encontramos cámara o micrófono. Conecta uno y pulsa «Intentar de nuevo». Si no puedes, avisa a tu profesorado.';
        } else if (name === 'NotReadableError' || name === 'TrackStartError') {
            message = 'La cámara la está usando otra aplicación (por ejemplo, una videollamada). Ciérrala y pulsa «Intentar de nuevo».';
        }
        this.renderShell('Cámara y micrófono', message);
        var panel = element(this.doc, 'div', 'o_irg_panel');
        panel.appendChild(element(this.doc, 'p', 'o_irg_error', message));
        var actions = element(this.doc, 'div', 'o_irg_actions');
        var again = button(this.doc, null, 'Intentar de nuevo');
        again.addEventListener('click', function () { self.showPermission(); });
        actions.appendChild(again);
        panel.appendChild(actions);
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.showCameraCheck = function () {
        var self = this;
        this.renderShell('Prueba de cámara y micrófono', 'Así te verá tu profesorado. Di algo en voz alta.');
        var panel = element(this.doc, 'div', 'o_irg_panel');
        panel.appendChild(element(this.doc, 'p', null, 'Así te verá tu profesorado. Di algo en voz alta: si la barra se mueve, te oímos bien.'));
        var preview = this.previewNode();
        panel.appendChild(preview);
        var meter = element(this.doc, 'div', 'o_irg_meter');
        meter.setAttribute('aria-hidden', 'true');
        var bar = element(this.doc, 'div', 'o_irg_meter_bar');
        meter.appendChild(bar);
        panel.appendChild(meter);
        var hint = element(this.doc, 'p', 'o_irg_warn', '');
        hint.hidden = true;
        panel.appendChild(hint);
        var picker = this.devicePicker();
        if (picker) {
            panel.appendChild(picker);
        }
        this.attachMeter(bar);
        this.win.setTimeout(function () {
            if (self.audioPeak >= 0 && self.audioPeak < 8) {
                hint.hidden = false;
                hint.textContent = 'No detectamos sonido. Comprueba que el micrófono no está silenciado.';
                self.setLive(hint.textContent);
            }
        }, 5000);
        var actions = element(this.doc, 'div', 'o_irg_actions');
        var ok = button(this.doc, null, 'Me veo y me oigo bien');
        ok.addEventListener('click', function () {
            self.index = 0;
            self.takes = [];
            self.showSegment();
        });
        actions.appendChild(ok);
        panel.appendChild(actions);
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.devicePicker = function () {
        var self = this;
        var media = this.win.navigator.mediaDevices;
        if (!media || !media.enumerateDevices) {
            return null;
        }
        var select = this.doc.createElement('select');
        select.hidden = true;
        media.enumerateDevices().then(function (devices) {
            var videos = (devices || []).filter(function (item) { return item.kind === 'videoinput'; });
            if (videos.length < 2) {
                return;
            }
            videos.forEach(function (item, index) {
                var option = self.doc.createElement('option');
                option.value = item.deviceId;
                option.textContent = item.label || ('Cámara ' + (index + 1));
                select.appendChild(option);
            });
            select.hidden = false;
        }).catch(function () {});
        select.addEventListener('change', function () {
            self.openStream({video: {deviceId: {exact: select.value}}, audio: true}).then(function () {
                self.showCameraCheck();
            }).catch(function (error) {
                self.showCameraError(error);
            });
        });
        return select;
    };

    OralCasePlayer.prototype.previewNode = function () {
        var preview = this.doc.createElement('video');
        preview.className = 'o_irg_preview o_irg_mirror';
        preview.autoplay = true;
        preview.muted = true;
        preview.playsInline = true;
        preview.setAttribute('playsinline', '');
        if (this.stream) {
            preview.srcObject = this.stream;
        }
        return preview;
    };

    OralCasePlayer.prototype.attachMeter = function (bar) {
        var self = this;
        var Ctx = this.win.AudioContext || this.win.webkitAudioContext;
        var tracks = this.stream ? this.stream.getAudioTracks() : [];
        if (!Ctx || !this.stream || !tracks.length) {
            this.audioPeak = tracks.length ? -1 : 0;
            return;
        }
        try {
            if (this.audioContext) {
                this.audioContext.close();
            }
            this.audioContext = new Ctx();
            if (this.audioContext.state === 'suspended' && this.audioContext.resume) {
                this.audioContext.resume();
            }
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 1024;
            this.audioContext.createMediaStreamSource(this.stream).connect(this.analyser);
            this.audioPeak = -1;
        } catch (error) {
            this.audioPeak = -1;
            return;
        }
        this.meterOn = true;
        var data = new this.win.Uint8Array(this.analyser.fftSize);
        var seen = false;
        var tick = function () {
            if (!self.meterOn || !self.analyser) {
                return;
            }
            self.analyser.getByteTimeDomainData(data);
            var peak = 0;
            for (var i = 0; i < data.length; i++) {
                var delta = Math.abs(data[i] - 128);
                if (delta > peak) {
                    peak = delta;
                }
            }
            if (!seen || peak > self.audioPeak) {
                seen = true;
                self.audioPeak = peak;
            }
            if (bar) {
                bar.style.width = Math.min(100, Math.round(peak * 1.5)) + '%';
            }
            self.win.requestAnimationFrame(tick);
        };
        this.win.requestAnimationFrame(tick);
    };

    OralCasePlayer.prototype.showSegment = function () {
        var segment = this.segments()[this.index];
        if (!segment) {
            this.showSummary();
            return;
        }
        this.blob = null;
        this.audioPeak = -1;
        if (segment.clip_url) {
            this.showClip(segment);
            return;
        }
        this.showPrompt(segment);
    };

    OralCasePlayer.prototype.segmentHeading = function (segment) {
        var total = this.segments().length;
        if (this.info && this.info.mode === 'clips') {
            return 'Tramo ' + segment.index + ' de ' + total + ' · ' + (segment.name || '');
        }
        return segment.name || 'Intervención';
    };

    OralCasePlayer.prototype.addProgress = function (panel) {
        if (!this.info || this.info.mode !== 'clips') {
            return;
        }
        var list = element(this.doc, 'div', 'o_irg_steps');
        list.setAttribute('role', 'progressbar');
        list.setAttribute('aria-valuemin', '1');
        list.setAttribute('aria-valuemax', String(this.segments().length));
        list.setAttribute('aria-valuenow', String(this.index + 1));
        list.setAttribute('aria-label', this.segmentHeading(this.segments()[this.index]));
        for (var i = 0; i < this.segments().length; i++) {
            var mark = element(this.doc, 'span');
            if (i < this.index) {
                mark.className = 'is-done';
            } else if (i === this.index) {
                mark.className = 'is-current';
            }
            list.appendChild(mark);
        }
        panel.appendChild(list);
    };

    OralCasePlayer.prototype.showClip = function (segment) {
        var self = this;
        var title = this.segmentHeading(segment);
        this.vimeoPlayer = null;
        this.vimeoReady = null;
        this.playback = null;
        this.renderShell(title, title);
        var panel = element(this.doc, 'div', 'o_irg_panel');
        this.addProgress(panel);
        var stage = element(this.doc, 'div', 'o_irg_stage');
        var play = button(this.doc, 'o_irg_play', 'Reproducir');
        var durationLine = element(this.doc, 'p', 'o_irg_note', '');
        var trouble = element(this.doc, 'p', 'o_irg_error', '');
        trouble.hidden = true;
        var skip = button(this.doc, 'o_irg_secondary', 'Responder ya');
        skip.hidden = true;
        var goPrompt = function () {
            self.clearTimers();
            self.showPrompt(segment);
        };
        var revealSkip = function (message) {
            if (!logic.shouldOfferSkip({failed: true})) {
                return;
            }
            trouble.hidden = false;
            trouble.textContent = message;
            skip.hidden = false;
            self.setLive(message);
        };
        skip.addEventListener('click', goPrompt);
        if (logic.isVimeoHost(segment.clip_url)) {
            this.mountVimeo(stage, segment, play, durationLine, revealSkip, goPrompt);
        } else if (logic.isSafeHttps(segment.clip_url)) {
            this.mountFile(stage, segment, play, durationLine, revealSkip, goPrompt);
        } else {
            revealSkip(LOAD_ERROR);
        }
        stage.appendChild(play);
        panel.appendChild(stage);
        panel.appendChild(durationLine);
        panel.appendChild(trouble);
        var actions = element(this.doc, 'div', 'o_irg_actions');
        actions.appendChild(this.transcriptButton(segment));
        actions.appendChild(skip);
        panel.appendChild(actions);
        this.root.appendChild(panel);
        this.win.setTimeout(function () {
            self.startPlayback(true);
        }, 250);
    };

    OralCasePlayer.prototype.mountVimeo = function (stage, segment, play, durationLine, revealSkip, goPrompt) {
        var self = this;
        var src = logic.vimeoSrc(segment.clip_url);
        if (!src) {
            revealSkip(LOAD_ERROR);
            return;
        }
        var frame = this.doc.createElement('iframe');
        frame.setAttribute('allow', 'autoplay; fullscreen; picture-in-picture');
        frame.title = 'Vídeo del tramo';
        frame.src = src;
        stage.appendChild(frame);
        var self = this;
        play.addEventListener('click', function () { self.startPlayback(false); });
        this.playback = {
            kind: 'vimeo',
            frame: frame,
            play: play,
            durationLine: durationLine,
            revealSkip: revealSkip,
            goPrompt: goPrompt,
            bound: false,
        };
    };

    OralCasePlayer.prototype.mountFile = function (stage, segment, play, durationLine, revealSkip, goPrompt) {
        var self = this;
        var video = this.doc.createElement('video');
        video.className = 'o_irg_clip';
        video.playsInline = true;
        video.preload = 'metadata';
        video.src = segment.clip_url;
        stage.appendChild(video);
        video.addEventListener('loadedmetadata', function () {
            var label = logic.clipDurationLabel(video.duration);
            if (label) {
                durationLine.textContent = label;
            }
        });
        video.addEventListener('ended', goPrompt);
        video.addEventListener('error', function () { revealSkip(LOAD_ERROR); });
        video.addEventListener('play', function () {
            play.hidden = true;
            self.armWatchdog(video.duration, goPrompt, revealSkip);
        });
        this.playback = {kind: 'file', video: video, play: play};
        play.addEventListener('click', function () { self.startPlayback(false); });
    };

    OralCasePlayer.prototype.startPlayback = function (silent) {
        var self = this;
        var playback = this.playback;
        if (!playback) {
            return;
        }
        if (playback.kind === 'file') {
            playback.video.play().then(function () {
                playback.play.hidden = true;
            }).catch(function () {
                if (!silent) {
                    playback.play.hidden = false;
                }
            });
            return;
        }
        if (!this.vimeoReady) {
            this.vimeoReady = loadVimeoApi(this.win, this.doc).then(function () {
                if (self.vimeoPlayer) {
                    return;
                }
                self.vimeoPlayer = new self.win.Vimeo.Player(playback.frame);
                self.vimeoPlayer.on('ended', playback.goPrompt);
                self.vimeoPlayer.on('error', function () { playback.revealSkip(LOAD_ERROR); });
                self.vimeoPlayer.on('play', function () {
                    playback.play.hidden = true;
                    self.armWatchdog(0, playback.goPrompt, playback.revealSkip);
                    self.vimeoPlayer.getDuration().then(function (duration) {
                        var label = logic.clipDurationLabel(duration);
                        if (label) {
                            playback.durationLine.textContent = label;
                        }
                        self.armWatchdog(duration, playback.goPrompt, playback.revealSkip);
                    }).catch(function () {});
                });
                self.vimeoPlayer.getTextTracks().then(function (tracks) {
                    if (tracks && tracks.length && tracks[0].language) {
                        return self.vimeoPlayer.enableTextTrack(tracks[0].language);
                    }
                    return null;
                }).catch(function () {});
            });
        }
        this.vimeoReady.then(function () {
            return self.vimeoPlayer.play();
        }).then(function () {
            if (playback.play) {
                playback.play.hidden = true;
            }
        }).catch(function () {
            if (!silent) {
                playback.revealSkip(LOAD_ERROR);
            }
        });
    };

    OralCasePlayer.prototype.armWatchdog = function (duration, goPrompt, revealSkip) {
        var ms = logic.watchdogMs(duration, true);
        if (!ms) {
            return;
        }
        if (this.watchTimer) {
            this.win.clearTimeout(this.watchTimer);
        }
        var self = this;
        this.watchTimer = this.win.setTimeout(function () {
            revealSkip(STALL_ERROR);
        }, ms);
        this.onLeave = function () {
            if (self.watchTimer) {
                self.win.clearTimeout(self.watchTimer);
                self.watchTimer = null;
            }
        };
    };

    OralCasePlayer.prototype.transcriptButton = function (segment) {
        var self = this;
        var control = button(this.doc, 'o_irg_secondary', 'Leer la transcripción');
        var region = element(this.doc, 'div', 'o_irg_panel');
        region.hidden = true;
        control.addEventListener('click', function () {
            region.hidden = !region.hidden;
            if (!region.hidden && !region.firstChild) {
                var text = (segment.transcript || '').trim();
                region.appendChild(element(
                    self.doc,
                    'p',
                    null,
                    text || 'Este tramo no tiene transcripción cargada. Puedes responder con lo que has visto.'
                ));
                self.root.appendChild(region);
            }
        });
        return control;
    };

    OralCasePlayer.prototype.showPrompt = function (segment) {
        var self = this;
        var title = this.segmentHeading(segment);
        this.renderShell(title, title);
        this.vimeoPlayer = null;
        this.playback = null;
        var panel = element(this.doc, 'div', 'o_irg_panel');
        this.addProgress(panel);
        if (segment.student_quote) {
            var quote = element(this.doc, 'blockquote', 'o_irg_quote');
            quote.textContent = '«' + segment.student_quote + '»';
            panel.appendChild(quote);
        }
        panel.appendChild(element(this.doc, 'p', null, logic.visibleStudentText(segment)));
        panel.appendChild(element(this.doc, 'p', 'o_irg_note', logic.responseLimitLabel(segment.max_seconds) + '. Tómate unos segundos para pensar antes de empezar.'));
        panel.appendChild(this.previewNode());
        this.mountListen(panel, segment);
        var actions = element(this.doc, 'div', 'o_irg_actions');
        logic.screenButtons('prompt').forEach(function (kind) {
            if (kind === 'record') {
                var record = button(self.doc, null, 'Grabar mi respuesta');
                record.addEventListener('click', function () { self.showRecording(segment); });
                actions.appendChild(record);
            }
        });
        if (segment.clip_url) {
            var again = button(this.doc, 'o_irg_secondary', 'Volver a ver el vídeo');
            again.addEventListener('click', function () { self.showClip(segment); });
            actions.appendChild(again);
        }
        actions.appendChild(this.transcriptButton(segment));
        panel.appendChild(actions);
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.mountListen = function (panel, segment) {
        var listen = segment.listen_clip_url || '';
        if (!logic.isSafeHttps(listen) || logic.isVimeoHost(listen)) {
            return;
        }
        var video = this.doc.createElement('video');
        video.className = 'o_irg_listen';
        video.muted = true;
        video.loop = true;
        video.playsInline = true;
        video.src = listen;
        video.play().catch(function () {});
        panel.appendChild(video);
    };

    OralCasePlayer.prototype.showRecording = function (segment) {
        var self = this;
        var title = this.segmentHeading(segment);
        this.renderShell(title, 'Grabando');
        this.dirty = true;
        this.audioPeak = -1;
        var panel = element(this.doc, 'div', 'o_irg_panel');
        this.addProgress(panel);
        var indicator = element(this.doc, 'p', 'o_irg_rec');
        indicator.setAttribute('role', 'status');
        var dot = element(this.doc, 'span', null, '● ');
        indicator.appendChild(dot);
        indicator.appendChild(this.doc.createTextNode('Grabando'));
        panel.appendChild(indicator);
        var timer = element(this.doc, 'p', 'o_irg_timer', '');
        timer.setAttribute('role', 'timer');
        timer.setAttribute('aria-live', 'off');
        panel.appendChild(timer);
        panel.appendChild(element(this.doc, 'p', 'o_irg_note', logic.visibleStudentText(segment)));
        var preview = this.previewNode();
        panel.appendChild(preview);
        var bar = element(this.doc, 'div', 'o_irg_meter_bar');
        this.attachMeter(bar);
        var actions = element(this.doc, 'div', 'o_irg_actions');
        var stop = null;
        logic.screenButtons('recording').forEach(function (kind) {
            if (kind === 'stop') {
                stop = button(self.doc, null, 'Terminar respuesta');
                stop.addEventListener('click', function () { self.stopRecorder(); });
                actions.appendChild(stop);
            }
        });
        panel.appendChild(actions);
        this.root.appendChild(panel);
        this.record(segment, indicator, timer, stop);
    };

    OralCasePlayer.prototype.record = function (segment, indicator, timer, stop) {
        var self = this;
        var chunks = [];
        var mime = logic.chooseRecorderMime(function (item) {
            return !!(self.win.MediaRecorder && self.win.MediaRecorder.isTypeSupported && self.win.MediaRecorder.isTypeSupported(item));
        });
        try {
            this.recorder = mime
                ? new this.win.MediaRecorder(this.stream, {mimeType: mime})
                : new this.win.MediaRecorder(this.stream);
        } catch (error) {
            this.showMessage('Tu navegador no permite grabar. Abre esta actividad en Chrome, Edge o Firefox actualizados.', true);
            return;
        }
        this.startedAt = Date.now();
        this.recorder.ondataavailable = function (event) {
            if (event.data && event.data.size) {
                chunks.push(event.data);
            }
        };
        this.recorder.onstop = function () {
            var canonical = logic.canonicalFromMime(self.recorder && self.recorder.mimeType) || {mime: 'video/webm', ext: 'webm'};
            self.ext = canonical.ext;
            self.duration = Math.max(0, Math.round((Date.now() - self.startedAt) / 1000));
            self.blob = new self.win.Blob(chunks, {type: canonical.mime});
            if (self.timer) {
                self.win.clearInterval(self.timer);
                self.timer = null;
            }
            self.showReview(segment);
        };
        this.recorder.start();
        var left = segment.max_seconds || this.info.max_duration_seconds;
        var flags = {};
        var opening = logic.countdownAnnouncement(left, flags);
        flags.started = true;
        if (opening) {
            this.setLive(opening.text);
        }
        var paint = function (value) {
            var label = 'Quedan ' + logic.formatTime(value);
            timer.textContent = label;
            indicator.appendChild(self.doc.createTextNode(''));
            var status = indicator.querySelector('span');
            indicator.textContent = '';
            if (status) {
                indicator.appendChild(status);
            } else {
                indicator.appendChild(element(self.doc, 'span', null, '● '));
            }
            indicator.appendChild(self.doc.createTextNode('Grabando · ' + label));
        };
        paint(left);
        this.timer = this.win.setInterval(function () {
            left -= 1;
            var announcement = logic.countdownAnnouncement(left, flags);
            if (announcement) {
                flags.announced15 = announcement.announced15 || flags.announced15;
                self.setLive(announcement.text);
            }
            paint(Math.max(left, 0));
            if (left <= 0) {
                if (stop) {
                    stop.disabled = true;
                }
                self.stopRecorder();
            }
        }, 1000);
    };

    OralCasePlayer.prototype.stopRecorder = function () {
        if (this.recorder && this.recorder.state === 'recording') {
            this.recorder.stop();
        }
    };

    OralCasePlayer.prototype.showReview = function (segment) {
        var self = this;
        var title = this.segmentHeading(segment);
        var spoken = 'Tu respuesta dura ' + logic.formatTime(this.duration) + '.';
        this.renderShell(title, spoken);
        var panel = element(this.doc, 'div', 'o_irg_panel');
        this.addProgress(panel);
        panel.appendChild(element(this.doc, 'p', null, 'Tu respuesta dura ' + logic.formatTime(this.duration) + '. Escúchala si quieres antes de seguir.'));
        if (this.duration < 10) {
            panel.appendChild(element(this.doc, 'p', 'o_irg_warn', 'Tu respuesta dura menos de 10 segundos. ¿Quieres repetirla?'));
        }
        var silent = this.audioPeak >= 0 && this.audioPeak < 8;
        if (silent) {
            panel.appendChild(element(this.doc, 'p', 'o_irg_warn', 'No se oye nada en esta respuesta. Revisa el micrófono y repítela.'));
        }
        if (this.blob) {
            var video = this.doc.createElement('video');
            video.className = 'o_irg_take';
            video.controls = true;
            video.playsInline = true;
            this.objectUrl = this.win.URL.createObjectURL(this.blob);
            video.src = this.objectUrl;
            panel.appendChild(video);
        }
        var actions = element(this.doc, 'div', 'o_irg_actions');
        var last = this.index >= this.segments().length - 1;
        var allowRetry = segment.allow_retry !== false || silent;
        logic.screenButtons('review', {allowRetry: allowRetry}).forEach(function (kind) {
            if (kind === 'use') {
                var use = button(self.doc, null, last ? 'Usar esta respuesta e ir al envío' : 'Usar esta respuesta y seguir');
                use.disabled = silent;
                use.addEventListener('click', function () { self.acceptTake(segment); });
                actions.appendChild(use);
            }
            if (kind === 'retry') {
                var retry = button(self.doc, 'o_irg_secondary', 'Repetir respuesta');
                retry.addEventListener('click', function () { self.confirmRetry(segment, panel); });
                actions.appendChild(retry);
            }
        });
        panel.appendChild(actions);
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.confirmRetry = function (segment, panel) {
        var self = this;
        if (logic.retryRestartsClip()) {
            this.showClip(segment);
            return;
        }
        var ask = element(this.doc, 'div', 'o_irg_panel');
        ask.appendChild(element(this.doc, 'p', null, 'Se borrará esta toma y grabarás otra. ¿Seguro?'));
        var actions = element(this.doc, 'div', 'o_irg_actions');
        var yes = button(this.doc, null, 'Sí, repetir');
        var no = button(this.doc, 'o_irg_secondary', 'No, mantenerla');
        yes.addEventListener('click', function () {
            self.blob = null;
            self.showPrompt(segment);
        });
        no.addEventListener('click', function () { ask.remove(); });
        actions.appendChild(yes);
        actions.appendChild(no);
        ask.appendChild(actions);
        panel.appendChild(ask);
    };

    OralCasePlayer.prototype.acceptTake = function (segment) {
        this.takes.push({
            index: segment.index,
            id: segment.id,
            name: segment.name,
            blob: this.blob,
            duration: this.duration,
            ext: this.ext,
        });
        this.dirty = true;
        this.index += 1;
        this.blob = null;
        if (this.index >= this.segments().length) {
            this.showSummary();
            return;
        }
        this.showSegment();
    };

    OralCasePlayer.prototype.showSummary = function () {
        var self = this;
        this.renderShell('Revisa antes de enviar', 'Revisa antes de enviar');
        var panel = element(this.doc, 'div', 'o_irg_panel');
        panel.appendChild(element(this.doc, 'p', null, 'Al enviar se mandan estas respuestas. La nota oficial la pone siempre tu profesorado.'));
        this.takes.forEach(function (take, position) {
            var row = element(self.doc, 'p', null, 'Tramo ' + take.index + ' · ' + logic.formatTime(take.duration) + ' ✓');
            panel.appendChild(row);
            var repeat = button(self.doc, 'o_irg_secondary', 'Repetir el tramo ' + take.index);
            repeat.addEventListener('click', function () {
                self.takes = self.takes.slice(0, position);
                self.index = position;
                self.showPrompt(self.segments()[position]);
            });
            panel.appendChild(repeat);
        });
        var actions = element(this.doc, 'div', 'o_irg_actions');
        var send = button(this.doc, null, 'Enviar mis ' + this.takes.length + ' respuestas');
        if (this.takes.length === 1) {
            send.textContent = 'Enviar mi respuesta';
        }
        send.addEventListener('click', function () { self.submitAll(); });
        actions.appendChild(send);
        panel.appendChild(actions);
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.submitAll = function () {
        var self = this;
        this.renderShell('Enviando tus respuestas…', 'Enviando tus respuestas… No cierres esta página.');
        var panel = element(this.doc, 'div', 'o_irg_panel');
        var status = element(this.doc, 'p', null, 'Enviando tus respuestas… 0 %. No cierres esta página.');
        var barWrap = element(this.doc, 'div', 'o_irg_upload');
        var bar = element(this.doc, 'span');
        barWrap.appendChild(bar);
        panel.appendChild(status);
        panel.appendChild(barWrap);
        this.root.appendChild(panel);
        var body = new this.win.FormData();
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
                var canonical = logic.canonicalFromMime(take.blob && take.blob.type) || {mime: 'video/webm', ext: take.ext || 'webm'};
                body.append('clip_' + take.index, take.blob, 'clip-' + take.index + '.' + canonical.ext);
            });
        } else if (this.takes[0]) {
            var one = logic.canonicalFromMime(this.takes[0].blob && this.takes[0].blob.type) || {mime: 'video/webm', ext: 'webm'};
            body.append('duracion_seg', String(this.takes[0].duration));
            body.append('video', this.takes[0].blob, 'caso.' + one.ext);
        }
        var xhr = new this.win.XMLHttpRequest();
        xhr.open('POST', this.info.submit_url);
        xhr.withCredentials = true;
        xhr.upload.onprogress = function (event) {
            if (!event.lengthComputable || !event.total) {
                return;
            }
            var pct = Math.min(100, Math.round((event.loaded * 100) / event.total));
            bar.style.width = pct + '%';
            status.textContent = 'Enviando tus respuestas… ' + pct + ' %. No cierres esta página.';
        };
        xhr.onerror = function () {
            self.showSubmitError('server_error');
        };
        xhr.onload = function () {
            readXhr(xhr).then(function (payload) {
                if (!payload || !payload.ok) {
                    self.showSubmitError(payload && payload.error);
                    return;
                }
                self.dirty = false;
                self.stopStream();
                self.showQueued(payload);
            });
        };
        xhr.send(body);
    };

    OralCasePlayer.prototype.showSubmitError = function (code) {
        var self = this;
        var message = logic.errorMessage(code);
        this.renderShell('No se ha podido enviar', message);
        var panel = element(this.doc, 'div', 'o_irg_panel');
        panel.appendChild(element(this.doc, 'p', 'o_irg_error', message));
        var actions = element(this.doc, 'div', 'o_irg_actions');
        if (code === 'session_expired') {
            var link = element(this.doc, 'a', null, 'Inicia sesión');
            link.href = '/web/login';
            actions.appendChild(link);
        } else if (code === 'invalid_csrf') {
            var reload = button(this.doc, null, 'Recargar');
            reload.addEventListener('click', function () { self.win.location.reload(); });
            actions.appendChild(reload);
        } else if (logic.canRetrySubmit(code)) {
            var retry = button(this.doc, null, 'Reintentar envío');
            retry.addEventListener('click', function () { self.submitAll(); });
            actions.appendChild(retry);
        } else if (code === 'missing_consent' || code === 'invalid_consent') {
            var back = button(this.doc, null, 'Volver al consentimiento');
            back.addEventListener('click', function () { self.showConsent(); });
            actions.appendChild(back);
        }
        panel.appendChild(actions);
        this.root.appendChild(panel);
    };

    OralCasePlayer.prototype.showQueued = function (payload) {
        var self = this;
        var message = 'Hemos recibido tus respuestas. Ahora se transcriben y la IA prepara una propuesta de puntuación para el profesorado. La nota oficial la pone siempre tu profesorado. Puedes cerrar esta página.';
        this.renderShell('Respuestas enviadas', message);
        var panel = element(this.doc, 'div', 'o_irg_panel');
        var text = element(this.doc, 'p', null, message);
        panel.appendChild(text);
        this.root.appendChild(panel);
        var polls = 0;
        var pull = function () {
            if (!payload.status_url || polls >= 8) {
                return;
            }
            polls += 1;
            self.win.fetch(payload.status_url, {credentials: 'same-origin'})
                .then(function (response) { return readPayload(response); })
                .then(function (body) {
                    var next = self.resultMessage(body);
                    if (next) {
                        text.textContent = next;
                        self.setLive(next);
                    }
                    if (body && (body.status === 'done' || body.status === 'completed' || body.status === 'scored' || body.status === 'error' || body.status === 'failed' || body.status === 'failure')) {
                        return;
                    }
                    self.pollTimer = self.win.setTimeout(pull, 5000);
                })
                .catch(function () {
                    self.pollTimer = self.win.setTimeout(pull, 5000);
                });
        };
        this.pollTimer = this.win.setTimeout(pull, 5000);
    };

    OralCasePlayer.prototype.resultMessage = function (body) {
        if (!body || body.error) {
            if (body && body.error === 'job_not_found') {
                return logic.errorMessage('job_not_found');
            }
            return null;
        }
        var status = body.status;
        if (status === 'done' || status === 'completed' || status === 'scored') {
            return 'Tu profesorado ya puede revisar tus respuestas. Verás la nota en el campus cuando la confirme.';
        }
        if (status === 'error' || status === 'failed' || status === 'failure') {
            if (this.info && this.info.keep_video) {
                return 'Tus respuestas se han recibido, pero no se ha podido preparar la propuesta automática. No tienes que hacer nada: tu profesorado las revisará directamente.';
            }
            return 'Tus respuestas se han recibido, pero no se ha podido preparar la propuesta automática y esta actividad no conserva la grabación en el campus. Avisa a tu profesorado para repetirla.';
        }
        return null;
    };

    OralCasePlayer.prototype.clearTimers = function () {
        if (this.timer) {
            this.win.clearInterval(this.timer);
            this.timer = null;
        }
        if (this.watchTimer) {
            this.win.clearTimeout(this.watchTimer);
            this.watchTimer = null;
        }
        if (this.pollTimer) {
            this.win.clearTimeout(this.pollTimer);
            this.pollTimer = null;
        }
    };

    OralCasePlayer.prototype.revokeTake = function () {
        if (this.objectUrl) {
            this.win.URL.revokeObjectURL(this.objectUrl);
            this.objectUrl = null;
        }
    };

    OralCasePlayer.prototype.stopStream = function () {
        this.meterOn = false;
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
            this.analyser = null;
        }
        if (!this.stream) {
            return;
        }
        this.stream.getTracks().forEach(function (track) { track.stop(); });
        this.stream = null;
    };

    function readPayload(response) {
        var url = response.url || '';
        if (url.indexOf('/web/login') !== -1) {
            return Promise.resolve({ok: false, error: 'session_expired'});
        }
        var type = (response.headers.get('content-type') || '').toLowerCase();
        if (type.indexOf('json') === -1) {
            return response.text().then(function (text) {
                if (text && text.indexOf('Session expired') !== -1) {
                    return {ok: false, error: 'invalid_csrf'};
                }
                return {ok: false, error: 'server_error'};
            });
        }
        return response.json().then(function (body) {
            return body || {ok: false, error: 'server_error'};
        });
    }

    function readXhr(xhr) {
        var text = xhr.responseText || '';
        if (text.indexOf('Session expired') !== -1) {
            return Promise.resolve({ok: false, error: 'invalid_csrf'});
        }
        try {
            return Promise.resolve(JSON.parse(text));
        } catch (error) {
            return Promise.resolve({ok: false, error: 'server_error'});
        }
    }

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

    return {
        isSafeHttps: logic && logic.isSafeHttps,
        isVimeoHost: logic && logic.isVimeoHost,
        vimeoSrc: logic && logic.vimeoSrc,
    };
});
