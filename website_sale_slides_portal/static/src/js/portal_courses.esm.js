import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";

export class CopyInvitationLink extends Interaction {
    static selector = ".js_copy_invitation_link";

    dynamicContent = {
        _root: {"t-on-click": this.onClick},
    };

    async onClick(ev) {
        const button = ev.currentTarget;
        const clipboard = browser.navigator.clipboard;
        if (!clipboard?.writeText) {
            return;
        }

        await this.waitFor(clipboard.writeText(button.dataset.clipboardText));
        button.textContent = _t("Copied");
        this.waitForTimeout(() => {
            button.textContent = _t("Copy link");
        }, 5000);
    }
}

registry
    .category("public.interactions")
    .add("website_sale_slides_portal.copy_invitation_link", CopyInvitationLink);
