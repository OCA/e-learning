# Copyright 2026 Graeme Gellatly <gdgellatly@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64

from odoo.tests.common import TransactionCase


class TestLocalVideoSlide(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.channel = cls.env["slide.channel"].create({"name": "Local video course"})

    def test_uploaded_file_is_a_local_video(self):
        slide = self.env["slide.slide"].create(
            {
                "name": "Local clip",
                "channel_id": self.channel.id,
                "slide_category": "video",
                "source_type": "local_file",
                "binary_content": base64.b64encode(b"\x00\x00"),
            }
        )
        self.assertEqual(slide.video_source_type, "local")
        self.assertEqual(slide.slide_type, "local_video")
        self.assertEqual(slide.slide_icon_class, "fa-file-video-o")
        self.assertIn(f"/slides/slide/{slide.id}/video_content", slide.embed_code)
        self.assertIn(f"/slides/slide/{slide.id}/captions.vtt", slide.embed_code)

    def test_youtube_without_a_file_stays_external(self):
        slide = (
            self.env["slide.slide"]
            .with_context(website_slides_skip_fetch_metadata=True)
            .create(
                {
                    "name": "YouTube clip",
                    "channel_id": self.channel.id,
                    "slide_category": "video",
                    "source_type": "local_file",
                    "video_url": "https://www.youtube.com/watch?v=ebBez6bcSEc",
                }
            )
        )
        self.assertEqual(slide.video_source_type, "youtube")
        self.assertEqual(slide.slide_type, "youtube_video")
        self.assertNotIn("/video_content", slide.embed_code or "")
