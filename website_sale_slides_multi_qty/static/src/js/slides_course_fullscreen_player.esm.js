import Fullscreen from "@website_slides/js/slides_course_fullscreen_player";
import {rpc} from "@web/core/network/rpc";

Fullscreen.include({
    init() {
        this._super.apply(this, arguments);
        this.publicKeyPromise = this._fetchPublicKeyAccess();
    },

    async _fetchPublicKeyAccess() {
        try {
            const data = await rpc("/slides/is_public_with_key", {});
            return data.is_public_with_key;
        } catch {
            return false;
        }
    },

    _onChangeSlide() {
        const superResult = this._super.apply(this, arguments);
        return Promise.all([Promise.resolve(superResult), this.publicKeyPromise]).then(
            ([, isPublicWithKey]) => {
                const slide = this._slideValue;
                if (!isPublicWithKey || !slide?._autoSetDone) {
                    return;
                }
                if (slide.category === "document") {
                    const iframe = this.el.querySelector(
                        "iframe.o_wslides_iframe_viewer"
                    );
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
            }
        );
    },
});
