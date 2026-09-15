import {Quiz} from "@website_slides/js/slides_course_quiz";
import {rpc} from "@web/core/network/rpc";

Quiz.include({
    willStart() {
        const superPromise = this._super(...arguments);
        const publicKeyPromise = rpc("/slides/is_public_with_key", {});

        return Promise.all([superPromise, publicKeyPromise]).then(([result, data]) => {
            if (data.is_public_with_key) {
                this.publicUser = false;
            }
            return result;
        });
    },
});
