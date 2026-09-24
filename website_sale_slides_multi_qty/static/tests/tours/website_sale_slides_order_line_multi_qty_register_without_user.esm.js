/** @odoo-module */
// Copyright 2025 Tecnativa - Pilar Vargas
/* License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {registry} from "@web/core/registry";

registry
    .category("web_tour.tours")
    .add("website_sale_slides_order_line_multi_qty_register_without_user", {
        test: true,
        steps: () => [
            {
                content: "Fill in the name",
                trigger: "#slide_channel_partner_name",
                run: "text My Test User",
            },
            {
                content: "Fill in the email",
                trigger: "#slide_channel_partner_email",
                run: "text testuser@example.com",
            },
            {
                content: "Fill in the phone",
                trigger: "#slide_channel_partner_phone",
                run: "text 123456789",
            },
            {
                content: "Fill in the identification number",
                trigger: 'input[name="identification_number"]',
                run: "text BE0477472701",
            },
            {
                content: "We accept the terms",
                trigger: "#accept_terms",
                run: "click",
            },
            {
                content: "Submit",
                trigger: "#join_course_submit",
            },
            {
                content: "It has been successfully enrolled.",
                trigger: ".o_wslides_js_channel_unsubscribe",
            },
        ],
    });
