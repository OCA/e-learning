# Copyright 2026 Graeme Gellatly <gdgellatly@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from markupsafe import Markup

from odoo import api, fields, models


class SlideSlide(models.Model):
    """Self-hosted video stored on the slide's existing ``binary_content``.

    A lesson is self-hosted when its category is video, its source is an
    uploaded file and that file is set. The file stays a normal attachment.
    """

    _inherit = "slide.slide"

    video_source_type = fields.Selection(
        selection_add=[("local", "Self-Hosted")],
    )
    captions_vtt = fields.Binary(
        "Captions (WebVTT)",
        attachment=True,
        help="Subtitles for a self-hosted video, shown as a CC track.",
    )
    slide_type = fields.Selection(
        selection_add=[("local_video", "Self-Hosted Video")],
        ondelete={"local_video": "set null"},
    )

    @api.depends("slide_category", "source_type", "binary_content")
    def _compute_video_source_type(self):
        res = super()._compute_video_source_type()
        for slide in self:
            if (
                slide.slide_category == "video"
                and slide.source_type == "local_file"
                and slide.binary_content
            ):
                slide.video_source_type = "local"
        return res

    @api.depends("video_source_type")
    def _compute_embed_code(self):
        res = super()._compute_embed_code()
        for slide in self:
            if slide.slide_category == "video" and slide.video_source_type == "local":
                # The style uses a literal "%". Old-style Markup formatting
                # reads "100%;" as a conversion specifier and crashes, so the
                # tag is built with an f-string. The id is an integer.
                url = f"/slides/slide/{slide.id}/video_content"
                captions = f"/slides/slide/{slide.id}/captions.vtt"
                video_tag = Markup(
                    '<video controls="controls" preload="metadata" '
                    f'style="width: 100%; height: 100%;" src="{url}">'
                    '<track kind="subtitles" srclang="en" label="English" '
                    f'src="{captions}"/>'
                    "</video>"
                )
                slide.embed_code = video_tag
                slide.embed_code_external = video_tag
        return res

    @api.depends("video_source_type")
    def _compute_slide_type(self):
        res = super()._compute_slide_type()
        for slide in self:
            if slide.slide_category == "video" and slide.video_source_type == "local":
                slide.slide_type = "local_video"
        return res

    @api.depends("slide_type")
    def _compute_slide_icon_class(self):
        res = super()._compute_slide_icon_class()
        for slide in self:
            if slide.slide_type == "local_video":
                slide.slide_icon_class = "fa-file-video-o"
        return res
