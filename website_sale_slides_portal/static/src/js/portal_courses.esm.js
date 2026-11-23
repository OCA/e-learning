/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CopyInvitationLink = publicWidget.Widget.extend({
    selector: ".js_copy_invitation_link",

    events: {
        click: "_onCopyInvitationLink",
    },

    async _onCopyInvitationLink(ev) {
        const button = ev.currentTarget;
        await browser.navigator.clipboard.writeText(button.dataset.clipboardText);
        button.textContent = _t("Copied");
        setTimeout(() => {
            button.textContent = _t("Copy link");
        }, 5000);
    },
});
