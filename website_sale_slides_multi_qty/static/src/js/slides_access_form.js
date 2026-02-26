odoo.define("website_sale_slides_multi_qty.slide_access_form", [], function () {
    "use strict";

    const toggle_key_access = $("#toggle_key_access");
    const $nameField = $("#slide_channel_partner_name");
    const $emailField = $("#slide_channel_partner_email");
    const $phoneField = $("#slide_channel_partner_phone");
    const $inputTermsCheckbox = $("#accept_terms");
    const $termsCheckbox = $("#terms_and_conditions");

    toggle_key_access.on("click", function () {
        $nameField.addClass("d-none").prop("required", false);
        $emailField.addClass("d-none").prop("required", false);
        $phoneField.addClass("d-none").prop("required", false);
        $termsCheckbox.addClass("d-none").prop("required", false);
        $inputTermsCheckbox.prop("required", false);
        toggle_key_access.addClass("d-none");
    });
});
