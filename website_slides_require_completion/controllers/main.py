# Copyright 2025 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.http import request, route

from odoo.addons.website_slides.controllers.main import WebsiteSlides


class WebsiteSlidesRequireCompletion(WebsiteSlides):
    @route(
        "/slides/channel/require_completion", type="json", auth="user", methods=["POST"]
    )
    def require_completion(self, slide_id):
        """
        Check if the chanell of the slide requires completion.
        """
        slide = request.env["slide.slide"].sudo().browse(slide_id)
        return {"is_required": slide.channel_id.require_slides_completion}
