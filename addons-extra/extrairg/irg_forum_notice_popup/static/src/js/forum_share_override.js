/** @odoo-module **/

/**
 * Simplify the standard website_forum "Thanks for posting!" social-share
 * modal so it only shows a confirmation message, without social-network
 * statistics or share icons.
 */

function simplifyForumShareModal(modal) {
    if (!modal || modal.id !== 'oe_social_share_modal') {
        return;
    }

    const title = modal.querySelector('.modal-title');
    if (title) {
        title.textContent = '¡Tu mensaje ha sido publicado!';
    }

    const body = modal.querySelector('.modal-body');
    if (body) {
        body.querySelectorAll('p').forEach((node) => node.remove());
        const message = document.createElement('p');
        message.textContent = 'Tu mensaje se ha publicado correctamente.';
        body.prepend(message);
    }

    const icons = modal.querySelector('.share-icons');
    if (icons) {
        icons.remove();
    }
}

document.addEventListener('shown.bs.modal', function (event) {
    simplifyForumShareModal(event.target);
});

const observer = new MutationObserver(function (mutations) {
    for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
            if (!(node instanceof HTMLElement)) {
                continue;
            }
            if (node.id === 'oe_social_share_modal') {
                simplifyForumShareModal(node);
            } else {
                const modal = node.querySelector && node.querySelector('#oe_social_share_modal');
                if (modal) {
                    simplifyForumShareModal(modal);
                }
            }
        }
    }
});

observer.observe(document.documentElement, { childList: true, subtree: true });
