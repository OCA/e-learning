/** @odoo-module */
// Copyright 2025 Tecnativa - Pilar Vargas
/* License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {registry} from "@web/core/registry";

registry
    .category("web_tour.tours")
    .add("website_sale_slides_order_line_multi_qty_join_without_user", {
        test: true,
        steps: () => [
            {
                content: "It is already joined.",
                trigger: "#toggle_key_access",
            },
            {
                content: "Fill in the identification number",
                trigger: 'input[name="identification_number"]',
                run: "text BE0477472701",
            },
            {
                content: "Submit",
                trigger: "#join_course_submit",
            },
            {
                content: "It has successfully accessed",
                trigger: ".o_wslides_js_channel_unsubscribe",
            },
        ],
    });
