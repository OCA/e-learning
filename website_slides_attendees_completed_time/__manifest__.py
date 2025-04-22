# Copyright 2025 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Website Slides Attendees Completed Time",
    "summary": """Show course completed time in attendee views""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Binhex,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/e-learning",
    "depends": ["website_slides"],
    "post_init_hook": "channel_partner_recompute_completion",
    "data": [
        "views/slide_channel_partner_views.xml",
    ],
    "demo": [],
}
