/** @odoo-module **/

import ajax from 'web.ajax';

function getCourseIdFromPath() {
    const match = window.location.pathname.match(/\/campus\/course\/(\d+)/);
    return match ? parseInt(match[1], 10) : null;
}

function getFirstCourseIdFromPage() {
    const links = document.querySelectorAll('a[href*="/campus/course/"]');
    for (const link of links) {
        const href = (link.getAttribute('href') || '').trim();
        const match = href.match(/\/campus\/course\/(\d+)/);
        if (match) {
            return parseInt(match[1], 10);
        }
    }
    return null;
}

function markSeen(courseId, noticeId) {
    window.localStorage.setItem(`irg_forum_notice_seen_${courseId}`, String(noticeId));
}

function alreadySeen(courseId, noticeId) {
    const stored = window.localStorage.getItem(`irg_forum_notice_seen_${courseId}`);
    return stored && stored === String(noticeId);
}

function closePopup(wrapper, courseId, noticeId) {
    markSeen(courseId, noticeId);
    wrapper.remove();
}

function renderPopup(courseId, notice) {
    if (!notice || !notice.id) {
        return;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'irg-forum-popup-wrap';
    wrapper.innerHTML = `
        <div class="irg-forum-popup-backdrop"></div>
        <div class="irg-forum-popup-card" role="dialog" aria-modal="true" aria-label="Aviso del foro">
            <button type="button" class="irg-forum-popup-close" aria-label="Cerrar">×</button>
            <div class="irg-forum-popup-badge">Aviso del foro</div>
            <h4 class="irg-forum-popup-title">${notice.title || 'Nuevo aviso'}</h4>
            ${notice.forum_name ? `<div class="irg-forum-popup-meta">Foro: ${notice.forum_name}</div>` : ''}
            ${notice.preview ? `<div class="irg-forum-popup-preview">${notice.preview}</div>` : ''}
            <div class="irg-forum-popup-actions">
                <button type="button" class="btn btn-secondary irg-forum-popup-dismiss">Cerrar</button>
                ${notice.url ? `<a class="btn btn-primary irg-forum-popup-open" href="${notice.url}">Ver aviso</a>` : ''}
            </div>
        </div>
    `;

    document.body.appendChild(wrapper);

    const closeBtn = wrapper.querySelector('.irg-forum-popup-close');
    const dismissBtn = wrapper.querySelector('.irg-forum-popup-dismiss');
    const backdrop = wrapper.querySelector('.irg-forum-popup-backdrop');
    const openBtn = wrapper.querySelector('.irg-forum-popup-open');

    [closeBtn, dismissBtn, backdrop].forEach((node) => {
        if (node) {
            node.addEventListener('click', () => closePopup(wrapper, courseId, notice.id));
        }
    });

    if (openBtn) {
        openBtn.addEventListener('click', () => markSeen(courseId, notice.id));
    }
}

async function initForumNoticePopup() {
    const courseId = getCourseIdFromPath() || getFirstCourseIdFromPage();
    if (!courseId) {
        return;
    }

    try {
        const result = await ajax.jsonRpc(`/campus/course/${courseId}/forum_notice_popup`, 'call', {});
        const notice = result && result.notice;
        if (!notice || !notice.id || alreadySeen(courseId, notice.id)) {
            return;
        }
        renderPopup(courseId, notice);
    } catch (error) {
        // noop
    }
}

document.addEventListener('DOMContentLoaded', initForumNoticePopup);
