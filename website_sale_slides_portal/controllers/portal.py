# Copyright 2026 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import http
from odoo.http import request
from odoo.osv import expression

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class CoursesCustomerPortal(CustomerPortal):
    def _prepare_courses_domain(self):
        partner = request.env.user.partner_id
        commercial = partner.commercial_partner_id
        base = [
            ("parent_id", "=", False),
            ("sale_order_line_ids", "!=", False),
        ]
        # Multi: visible for the whole commercial entity
        multi = [
            ("partner_id.commercial_partner_id", "=", commercial.id),
            ("available_registrations", ">", 1),
        ]
        # Single: visible only for the current partner
        individual = [
            ("partner_id", "=", partner.id),
            ("available_registrations", "=", 1),
        ]
        return expression.AND([base, expression.OR([multi, individual])])

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "courses_count" in counters:
            domain = self._prepare_courses_domain()
            values["courses_count"] = (
                request.env["slide.channel.partner"].sudo().search_count(domain)
            )
        return values

    @http.route(["/my/courses"], type="http", auth="user", website=True)
    def portal_my_courses(
        self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_values()
        SlideChannelPartner = request.env["slide.channel.partner"]
        domain = self._prepare_courses_domain()
        searchbar_sortings = self._prepare_searchbar_sortings()
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]
        courses_count = SlideChannelPartner.sudo().search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/courses",
            url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
            total=courses_count,
            page=page,
            step=self._items_per_page,
        )
        courses = SlideChannelPartner.sudo().search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        values.update(
            {
                "courses": courses,
                "page_name": "courses",
                "default_url": "/my/courses",
                "pager": pager,
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("website_sale_slides_portal.portal_my_courses", values)
