# Copyright 2026 Graeme Gellatly <gdgellatly@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64

from odoo import http
from odoo.http import request

from odoo.addons.website_slides.controllers.main import (
    WebsiteSlides,
    handle_wslide_error,
)


class WebsiteSlidesVideoLocal(WebsiteSlides):
    @http.route(
        '/slides/slide/<model("slide.slide"):slide>/video_content',
        type="http",
        auth="public",
        website=True,
        sitemap=False,
        handle_params_access_error=handle_wslide_error,
    )
    def slide_get_video_content(self, slide):
        """Stream the uploaded video.

        ``ir.binary`` answers HTTP Range requests, so the player can seek
        without downloading the file from the start. Access is the same
        check website_slides uses for a slide PDF.
        """
        return (
            request.env["ir.binary"]
            ._get_stream_from(slide, "binary_content")
            .get_response()
        )

    @http.route(
        '/slides/slide/<model("slide.slide"):slide>/captions.vtt',
        type="http",
        auth="public",
        website=True,
        sitemap=False,
        handle_params_access_error=handle_wslide_error,
    )
    def slide_get_captions(self, slide):
        """WebVTT captions, or an empty track when the lesson has none."""
        if slide.captions_vtt:
            body = base64.b64decode(slide.captions_vtt)
        else:
            body = b"WEBVTT\n\n"
        return request.make_response(
            body,
            headers=[
                ("Content-Type", "text/vtt; charset=utf-8"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "private, max-age=300"),
            ],
        )
