/** @odoo-module **/

/**
 * Override the standard website_forum "Thanks for posting!" social-share
 * modal so it only shows a simple confirmation message without the
 * social-media statistics text or share icons.
 */

import { qweb } from 'web.core';

// ── Override the three sub-templates that carry the social-media copy ──

qweb.add_templates(`
<templates>
    <t t-name="website.social_modal" t-extend="website.social_modal">
        <t t-jquery=".modal-title" t-operation="inner">
            ¡Tu mensaje ha sido publicado!
        </t>
    </t>

    <t t-name="website_forum.social_message_question">
        <p>Tu pregunta se ha publicado correctamente.</p>
    </t>

    <t t-name="website_forum.social_message_answer">
        <p>Tu respuesta se ha publicado correctamente.</p>
    </t>

    <t t-name="website_forum.social_message_default">
        <p>Tu publicación se ha registrado correctamente.</p>
    </t>
</templates>
`);

// Hide the share icons via DOM after the modal is shown
document.addEventListener('shown.bs.modal', function (ev) {
    if (ev.target && ev.target.id === 'oe_social_share_modal') {
        const icons = ev.target.querySelector('.share-icons');
        if (icons) {
            icons.style.display = 'none';
        }
    }
});
