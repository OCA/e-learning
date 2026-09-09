/** @odoo-module **/
import {SIZES, utils as uiUtils} from "@web/core/ui/ui_service";

import Fullscreen from "@website_slides/js/slides_course_fullscreen_player";

Fullscreen.include({
    init: function () {
        this._super.apply(this, arguments);
        this.isPublicWithKey = false;
        this._fetchSessionData().then((isPublicWithKey) => {
            this.isPublicWithKey = isPublicWithKey;
        });
        this.rpc = this.bindService("rpc");
    },
    /**
     * Checks if the user is public with password by calling the method in the backend.
     *
     * @returns {Promise<Boolean>}
     * @private
     */
    _fetchSessionData: function () {
        return this.rpc("/slides/is_public_with_key")
            .then((data) => {
                return (
                    data.invite_hash &&
                    data.identification_number &&
                    data.invite_partner_id
                );
            })
            .catch(() => {
                return false;
            });
    },
    /**
     * Override methods to execute logic for public users with passwords
     * @override
     * @private
     */
    _onChangeSlide: function () {
        if (this.isPublicWithKey) {
            var self = this;
            var slide = this.get("slide");
            self._pushUrlState();
            return this._fetchSlideContent()
                .then(function () {
                    var websiteName = document.title.split(" | ")[1]; // Get the website name from title
                    document.title = websiteName
                        ? slide.name + " | " + websiteName
                        : slide.name;
                    if (uiUtils.getSize() < SIZES.MD) {
                        self._toggleSidebar(); // Hide sidebar when small device screen
                    }
                    return self._renderSlide();
                })
                .then(function () {
                    if (slide._autoSetDone) {
                        // No useless RPC call
                        if (slide.category === "document") {
                            // Only set the slide as completed after iFrame is loaded to avoid concurrent execution with 'embedUrl' controller
                            self.el
                                .querySelector("iframe.o_wslides_iframe_viewer")
                                .addEventListener("load", () =>
                                    self._toggleSlideCompleted(slide)
                                );
                        } else {
                            return self._toggleSlideCompleted(slide);
                        }
                    }
                });
        }
        return this._super.apply(this, arguments);
    },
    // /**
    //  * @override
    //  * @private
    //  */
    // _onSlideToComplete: function (ev) {
    //     if (this.isPublicWithKey) {
    //         var slideId = ev.data.id;
    //         this._setCompleted(slideId);
    //     }
    //     return this._super.apply(this, arguments);
    // },
});
