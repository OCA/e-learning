/** @odoo-module */
// Copyright 2025 Tecnativa - Pilar Vargas
/* License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("website_sale_slides_order_line_multi_qty", {
    test: true,
    url: "/slides",
    steps: () => [
        {
            content: "Select the course",
            trigger: 'a:contains("Test Channel")',
        },
        {
            content: "Add a course to the cart",
            trigger: "a#add_to_cart",
        },
        {
            content: "Add another course to the cart",
            trigger: "a#add_to_cart",
        },
        {
            content: "Add one more course to the cart",
            trigger: "a#add_to_cart",
        },
        {
            content: "Go to cart",
            trigger: "a[href='/shop/cart']",
            extra_trigger: "sup.my_cart_quantity:contains('3')",
        },
        {
            trigger: ".btn:contains('Checkout')",
        },
    ],
});
