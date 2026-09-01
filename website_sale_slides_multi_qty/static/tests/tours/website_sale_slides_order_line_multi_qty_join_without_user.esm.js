// Copyright 2025 Tecnativa - Pilar Vargas
/* License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {registry} from "@web/core/registry";
import {clickOnElement} from "@website/js/tours/tour_utils";

registry
    .category("web_tour.tours")
    .add("website_sale_slides_order_line_multi_qty_join_without_user", {
        steps: () => [
            clickOnElement("It is already joined.", "#toggle_key_access"),
            {
                content: "Fill in the identification number",
                trigger: 'input[name="identification_number"]',
                run: "edit BE0477472701",
            },
            {
                content: "Submit",
                trigger: "#join_course_submit",
                run: "click",
                expectUnloadPage: true,
            },
            {
                content: "It has successfully accessed",
                trigger: ".o_wslides_js_channel_unsubscribe",
            },
        ],
    });

registry
    .category("web_tour.tours")
    .add("website_sale_slides_order_line_multi_qty_join_registered_user", {
        steps: () => [
            {
                content: "Join the course as a registered user",
                trigger: 'a[href*="/join?invite_partner_id="]',
                run: "click",
                expectUnloadPage: true,
            },
            {
                content: "The registered user has successfully joined",
                trigger: ".o_wslides_js_channel_unsubscribe",
            },
        ],
    });

registry
    .category("web_tour.tours")
    .add("website_sale_slides_order_line_multi_qty_registered_user_login", {
        steps: () => [
            clickOnElement("existing participation access", "#toggle_key_access"),
            {
                content: "Fill in the registered identification number",
                trigger: 'input[name="identification_number"]',
                run: "edit BE0477472701",
            },
            {
                content: "Submit the identification number",
                trigger: "#join_course_submit",
                run: "click",
                expectUnloadPage: true,
            },
            {
                content: "The participant must log in",
                trigger: '.alert-warning a[href^="/web/login"]',
            },
        ],
    });
