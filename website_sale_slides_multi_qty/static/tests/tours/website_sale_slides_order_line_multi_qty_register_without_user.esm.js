// Copyright 2025 Tecnativa - Pilar Vargas
/* License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {registry} from "@web/core/registry";
import {clickOnElement} from "@website/js/tours/tour_utils";

registry
    .category("web_tour.tours")
    .add("website_sale_slides_order_line_multi_qty_register_without_user", {
        steps: () => [
            {
                content: "Fill in the name",
                trigger: "#slide_channel_partner_name",
                run: "edit My Test User",
            },
            {
                content: "Fill in the email",
                trigger: "#slide_channel_partner_email",
                run: "edit testuser@example.com",
            },
            {
                content: "Fill in the phone",
                trigger: "#slide_channel_partner_phone",
                run: "edit 123456789",
            },
            {
                content: "Fill in the identification number",
                trigger: 'input[name="identification_number"]',
                run: "edit BE0477472701",
            },
            clickOnElement("We accept the terms", "#accept_terms"),
            {
                content: "Submit",
                trigger: "#join_course_submit",
                run: "click",
                expectUnloadPage: true,
            },
            {
                content: "It has been successfully enrolled.",
                trigger: ".o_wslides_js_channel_unsubscribe",
            },
        ],
    });
