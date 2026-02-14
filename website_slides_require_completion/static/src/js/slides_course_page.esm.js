/** @odoo-module **/

import {SlideCoursePage} from "@website_slides/js/slides_course_page";
import {patch} from "@web/core/utils/patch";
patch(
    SlideCoursePage.prototype,
    "website_slides_require_completion.slides_course_page",
    {
        toggleCompletionButton: function (slide, completed = true) {
            this._super.apply(this, arguments);
            const self = this;
            this._rpc({
                route: "/slides/channel/require_completion",
                params: {slide_id: slide.id},
            })
                .then((data) => {
                    if (
                        self._parseBoolean(slide.completed) != completed &&
                        data.is_required
                    ) {
                        window.location.reload();
                    }
                })
                .guardedCatch((err) => {
                    console.error("ERROR en RPC:", err);
                });
        },

        _parseBoolean: function (str) {
            return typeof str === "string" && str.toLowerCase() === "true";
        },
    }
);
