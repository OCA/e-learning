# Copyright 2025 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.addons.website_slides.tests.common import SlidesCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestSlideRequireCompletion(SlidesCase, HttpCase):
    def test_01_require_completion(self):
        self.channel.write({"require_slides_completion": True})
        self.slide._compute_is_blocked()
        self.assertFalse(self.slide.is_blocked)
        self.slide_2._compute_is_blocked()
        self.assertTrue(self.slide_2.is_blocked)

    def test_02_require_completion_previous_slide_completed(self):
        self.channel.write({"require_slides_completion": True})
        self.authenticate("admin", "admin")
        data = json.dumps(
            {
                "id": 0,
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"slide_id": self.slide_2.id},
            }
        ).encode()
        response = self.url_open(
            "/slides/channel/require_completion",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        result = response.json()["result"]
        self.assertEqual(result, {"is_required": True})
