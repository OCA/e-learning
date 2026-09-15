// Copyright 2025 Tecnativa - Pilar Vargas
/* License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {clickOnElement} from "@website/js/tours/tour_utils";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

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
            {
                content: "Complete, vote and uncomplete a course slide",
                trigger: 'a[title="How To Cook Humans"]',
                run: async (helpers) => {
                    const slideId = Number(
                        new URL(helpers.anchor.href).pathname.match(/-(\d+)$/)?.[1]
                    );
                    if (!slideId) {
                        throw new Error("The course slide ID could not be determined");
                    }
                    const completed = await rpc("/slides/slide/set_completed", {
                        slide_id: slideId,
                    });
                    if (completed.error) {
                        throw new Error(completed.error);
                    }
                    const vote = await rpc("/slides/slide/like", {
                        slide_id: slideId,
                        upvote: true,
                    });
                    if (vote.error) {
                        throw new Error(vote.error);
                    }
                    const uncompleted = await rpc("/slides/slide/set_uncompleted", {
                        slide_id: slideId,
                    });
                    if (uncompleted.error) {
                        throw new Error(uncompleted.error);
                    }
                },
            },
            {
                content: "Open the quiz",
                trigger:
                    'a[href*="/slides/slide/"]' +
                    '[href*="how-to-cook-humans-for-humans-"]',
                run: "click",
                expectUnloadPage: true,
            },
            {
                content: "The anonymous participant can answer the quiz",
                trigger: ".o_wslides_js_lesson_quiz_submit",
                run: async (helpers) => {
                    const quiz = document.querySelector(".o_wslides_js_lesson_quiz");
                    const answers = [
                        ...document.querySelectorAll(".o_wslides_quiz_answer"),
                    ];
                    const slideId = Number(quiz.dataset.id);
                    const incorrectAnswerId = Number(answers.at(-1).dataset.answerId);
                    const correctAnswerId = Number(answers[0].dataset.answerId);

                    const incorrectResult = await rpc("/slides/slide/quiz/submit", {
                        slide_id: slideId,
                        answer_ids: [incorrectAnswerId],
                    });
                    if (incorrectResult.error) {
                        throw new Error(incorrectResult.error);
                    }

                    const correctResult = await rpc("/slides/slide/quiz/submit", {
                        slide_id: slideId,
                        answer_ids: [correctAnswerId],
                    });
                    if (correctResult.error || !correctResult.completed) {
                        throw new Error(
                            correctResult.error || "The quiz was not completed"
                        );
                    }

                    helpers.anchor.classList.add("o_anonymous_course_flow_completed");
                },
            },
            {
                content: "The anonymous course flow has finished",
                trigger:
                    ".o_wslides_js_lesson_quiz_submit" +
                    ".o_anonymous_course_flow_completed",
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

registry
    .category("web_tour.tours")
    .add("website_sale_slides_multi_qty_buyer_already_enrolled", {
        steps: () => [
            {
                content:
                    "The buyer remains enrolled after creating the registration pool",
                trigger: ".o_wslides_js_channel_unsubscribe",
                run() {
                    if (document.querySelector(".o_wslides_js_channel_join")) {
                        throw new Error(
                            "Join Course is available for an enrolled buyer"
                        );
                    }
                },
            },
        ],
    });
