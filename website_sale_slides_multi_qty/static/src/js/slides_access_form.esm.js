import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteSaleSlidesMultiQtyAccessForm = publicWidget.Widget.extend({
    selector: 'form[action="/slides/channel/join_with_id"]',
    events: {
        "click #toggle_key_access": "_onToggleKeyAccess",
    },

    _onToggleKeyAccess() {
        this.$("#slide_channel_partner_name")
            .addClass("d-none")
            .prop("required", false);
        this.$("#slide_channel_partner_email")
            .addClass("d-none")
            .prop("required", false);
        this.$("#slide_channel_partner_phone")
            .addClass("d-none")
            .prop("required", false);
        this.$("#terms_and_conditions").addClass("d-none");
        this.$("#accept_terms").prop("required", false);
        this.$("#toggle_key_access").addClass("d-none");
    },
});
