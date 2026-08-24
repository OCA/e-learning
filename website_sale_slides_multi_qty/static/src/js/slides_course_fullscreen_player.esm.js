import Fullscreen from "@website_slides/js/slides_course_fullscreen_player";
import {rpc} from "@web/core/network/rpc";

Fullscreen.include({
    init() {
        this._super.apply(this, arguments);
        this.isPublicWithKey = false;
        this._fetchSessionData().then((isPublicWithKey) => {
            this.isPublicWithKey = isPublicWithKey;
        });
    },

    async _fetchSessionData() {
        try {
            const data = await rpc("/slides/is_public_with_key", {});
            return Boolean(
                data.invite_hash && data.identification_number && data.invite_partner_id
            );
        } catch {
            return false;
        }
    },

    _onChangeSlide() {
        const superResult = this._super.apply(this, arguments);
        return Promise.resolve(superResult).then(() => {
            const slide = this._slideValue;
            if (!this.isPublicWithKey || !slide?._autoSetDone) {
                return;
            }

            if (slide.category === "document") {
                const iframe = this.el.querySelector("iframe.o_wslides_iframe_viewer");
                if (iframe) {
                    iframe.addEventListener(
                        "load",
                        () => this._toggleSlideCompleted(slide),
                        {once: true}
                    );
                }
                return;
            }

            return this._toggleSlideCompleted(slide);
        });
    },
});
