/* Extend the fullscreen player for a self-hosted video.
 *
 * The core player only renders youtube, vimeo and google_drive. Any other
 * videoSourceType leaves the content area empty, even when embed_code is
 * set. Same extension point as website_slides_survey for certification.
 */
import Fullscreen from "@website_slides/js/slides_course_fullscreen_player";
import {renderToElement} from "@web/core/utils/render";

Fullscreen.include({
    /**
     * @override
     * Local videos have no player completion event, so opening the slide
     * marks it done, as Google Drive videos already do.
     */
    _preprocessSlideData: function (slidesDataList) {
        const result = this._super(slidesDataList);
        result.forEach((slideData) => {
            if (
                !slideData.hasQuestion &&
                slideData.category === "video" &&
                slideData.videoSourceType === "local"
            ) {
                slideData._autoSetDone = true;
            }
        });
        return result;
    },

    /**
     * @override
     */
    _renderSlide: function () {
        const def = this._super.apply(this, arguments);
        if (
            this._slideValue.category === "video" &&
            this._slideValue.videoSourceType === "local"
        ) {
            const contentEl = this.el.querySelector(".o_wslides_fs_content");
            contentEl.textContent = "";
            contentEl.append(
                renderToElement("website_slides_video_local.fullscreen_video_local", {
                    widget: this,
                })
            );
        }
        return Promise.all([def]);
    },
});
