# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import http
from odoo.http import request

from odoo.addons.website_slides_survey.controllers.slides import WebsiteSlidesSurvey


class WebsiteSlidesSurvey(WebsiteSlidesSurvey):
    @http.route(
        ["/slides_survey/slide/get_certification_url"],
        type="http",
        auth="public",
        website=True,
    )
    def slide_get_certification_url(self, slide_id, **kw):
        invite_hash = request.session.get("invite_hash", False)
        identification_number = (request.session.get("identification_number", False),)
        invite_partner_id = request.session.get("invite_partner_id", False)
        res = super().slide_get_certification_url(slide_id=slide_id, **kw)
        if request.env.user._is_public() and not (
            identification_number and invite_partner_id and invite_hash
        ):
            return request.redirect("/web/login")
        return res
