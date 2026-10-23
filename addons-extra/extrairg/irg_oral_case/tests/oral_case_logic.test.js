'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const test = require('node:test');
const vm = require('vm');

const root = path.resolve(__dirname, '..');
const logicPath = path.join(root, 'static', 'src', 'js', 'oral_case_logic.js');
const playerPath = path.join(root, 'static', 'src', 'js', 'oral_case_player.js');
const cssPath = path.join(root, 'static', 'src', 'css', 'oral_case_player.css');

function loadLogic() {
    const context = {URL: URL};
    context.globalThis = context;
    vm.createContext(context);
    vm.runInContext(fs.readFileSync(logicPath, 'utf8'), context, {filename: logicPath});
    return context.IrgOralCaseLogic;
}

test('logic module exports the widget decisions', () => {
    const logic = loadLogic();
    assert.equal(typeof logic.chooseRecorderMime, 'function');
    assert.equal(typeof logic.screenButtons, 'function');
    assert.equal(typeof logic.errorMessage, 'function');
    assert.equal(logic.retryRestartsClip(), false);
});

test('recorder prefers webm and falls back to mp4', () => {
    const logic = loadLogic();
    assert.equal(
        logic.chooseRecorderMime((mime) => mime === 'video/webm'),
        'video/webm',
    );
    assert.equal(
        logic.chooseRecorderMime((mime) => mime === 'video/mp4'),
        'video/mp4',
    );
    assert.equal(logic.chooseRecorderMime(() => false), '');
    assert.deepEqual(logic.canonicalFromMime('video/mp4;codecs=avc1'), {
        mime: 'video/mp4',
        ext: 'mp4',
    });
    assert.deepEqual(logic.canonicalFromMime('video/webm'), {
        mime: 'video/webm',
        ext: 'webm',
    });
    assert.equal(logic.canonicalFromMime('text/html'), null);
});

test('review screen does not keep record or stop, and retry does not restart the clip', () => {
    const logic = loadLogic();
    const review = logic.screenButtons('review', {allowRetry: true});
    assert.deepEqual(review, ['use', 'retry']);
    assert.equal(review.includes('record'), false);
    assert.equal(review.includes('stop'), false);
    assert.deepEqual(logic.screenButtons('recording'), ['stop']);
    assert.equal(logic.retryRestartsClip(), false);
});

test('clip duration is shown only when the player reports it', () => {
    const logic = loadLogic();
    assert.equal(logic.clipDurationLabel(null), null);
    assert.equal(logic.clipDurationLabel(0), null);
    assert.equal(logic.clipDurationLabel(Number.NaN), null);
    assert.equal(logic.clipDurationLabel(53), 'El vídeo dura 0:53');
    assert.equal(logic.responseLimitLabel(90), 'Tiempo máximo: 1:30');
});

test('countdown is announced at the start, at 15 seconds and at the end', () => {
    const logic = loadLogic();
    assert.equal(logic.countdownAnnouncement(90, {}).text, 'Grabando. Quedan 1:30.');
    const mid = logic.countdownAnnouncement(40, {started: true});
    assert.equal(mid, null);
    const fifteen = logic.countdownAnnouncement(15, {started: true, announced15: false});
    assert.equal(fifteen.text, 'Quedan 15 segundos.');
    assert.equal(fifteen.announced15, true);
    assert.equal(
        logic.countdownAnnouncement(15, {started: true, announced15: true}),
        null,
    );
    assert.equal(
        logic.countdownAnnouncement(0, {started: true, announced15: true}).text,
        'Has llegado al tiempo máximo. Tu respuesta se ha guardado.',
    );
});

test('skip control waits for an error or for playback to run past the clip', () => {
    const logic = loadLogic();
    assert.equal(logic.shouldOfferSkip({playbackStarted: false, failed: false}), false);
    assert.equal(logic.shouldOfferSkip({playbackStarted: false, failed: true}), true);
    assert.equal(logic.watchdogMs(40, false), null);
    assert.equal(logic.watchdogMs(40, true), 55000);
    assert.equal(logic.watchdogMs(0, true), 90000);
});

test('student text hides the AI prompt, and API errors stay in Spanish', () => {
    const logic = loadLogic();
    assert.equal(
        logic.visibleStudentText({student_text: 'Responde breve.', prompt: 'Indicadores secretos'}),
        'Responde breve.',
    );
    assert.equal(
        logic.visibleStudentText({student_text: '  ', prompt: 'Texto antiguo'}),
        'Texto antiguo',
    );
    assert.equal(logic.errorMessage('invalid_video_type').includes('JSON'), false);
    assert.match(logic.errorMessage('invalid_video_type'), /formato/i);
    assert.match(logic.errorMessage('n8n_unavailable'), /inténtalo de nuevo/i);
    assert.equal(logic.canRetrySubmit('n8n_unavailable'), true);
    assert.equal(logic.canRetrySubmit('invalid_video_type'), false);
    assert.equal(logic.errorMessage('score_ia'), 'No se ha podido enviar la intervención.');
});

test('vimeo urls keep the privacy hash and reject other hosts', () => {
    const logic = loadLogic();
    const src = logic.vimeoSrc('https://player.vimeo.com/video/999?h=abc');
    assert.equal(src, 'https://player.vimeo.com/video/999?h=abc');
    assert.equal(logic.isVimeoHost('https://player.vimeo.com/video/1?h=abc'), true);
    assert.equal(logic.isVimeoHost('https://evil.example/player.vimeo.com'), false);
    assert.equal(logic.isSafeHttps('javascript:alert(1)'), false);
    assert.equal(logic.vimeoSrc('https://cdn.example.test/clip.mp4'), null);
    assert.equal(logic.isVimeoHost('https://www.vimeo.com/123456'), true);
    assert.equal(
        logic.vimeoSrc('https://www.vimeo.com/123456/abcdef'),
        'https://player.vimeo.com/video/123456?h=abcdef',
    );
});

test('player source boots inside a same-origin iframe and does not build HTML strings', () => {
    const player = fs.readFileSync(playerPath, 'utf8');
    const css = fs.readFileSync(cssPath, 'utf8');
    assert.equal(player.includes('innerHTML'), false);
    assert.equal(player.includes('contentDocument'), true);
    assert.equal(/(^|[^.])clearInterval\(/.test(player), false);
    assert.equal(/(^|[^.])clearTimeout\(/.test(player), false);
    assert.equal(player.includes('this.win.clearInterval'), true);
    assert.equal(player.includes('this.win.clearTimeout'), true);
    assert.equal(player.includes('MutationObserver'), true);
    assert.equal(player.includes('MediaRecorder'), true);
    assert.equal(player.includes('pending_legal_review'), true);
    assert.equal(player.includes('pendiente de validación legal'), true);
    assert.equal(player.includes('Responder ya'), true);
    assert.equal(player.includes('Grabando'), true);
    assert.equal(player.includes('Repetir respuesta'), true);
    assert.equal(player.includes('slides_course_fullscreen_player'), false);
    assert.match(css, /56\.25%/);
    assert.match(css, /#074A86/);
    assert.equal(css.includes('#0f766e'), false);
});
