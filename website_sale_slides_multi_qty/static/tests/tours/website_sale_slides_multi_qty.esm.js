// Copyright 2025 Tecnativa - Pilar Vargas
/* License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {registry} from "@web/core/registry";
import {clickOnElement} from "@website/js/tours/tour_utils";
import * as tourUtils from "@website_sale/js/tours/tour_utils";

registry.category("web_tour.tours").add("website_sale_slides_order_line_multi_qty", {
    url: "/slides",
    steps: () => [
        ...tourUtils.addToCart({
            productName: "Test Channel",
            search: false,
            expectUnloadPage: true,
        }),
        {
            content: "Wait for the first course to be added",
            trigger: "a sup.my_cart_quantity:text(1)",
        },
        clickOnElement("Add another course to the cart", "a#add_to_cart"),
        {
            content: "Wait for the second course to be added",
            trigger: "a sup.my_cart_quantity:text(2)",
        },
        clickOnElement("Add one more course to the cart", "a#add_to_cart"),
        tourUtils.goToCart({quantity: 3}),
        tourUtils.goToCheckout(),
    ],
});
