from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.website_slides.tests import common


@tagged("-at_install", "post_install")
class TestAttendeesCompletedTime(common.SlidesCase):
    @mute_logger("odoo.models")
    def test_channel_attendees_completed_time(self):
        channel_publisher = self.channel.with_user(self.user_officer)
        channel_publisher.write(
            {
                "enroll": "invite",
            }
        )
        channel_publisher._action_add_members(self.user_emp.partner_id)
        self.channel.with_user(self.user_emp)

        members = self.env["slide.channel.partner"].search(
            [("channel_id", "=", self.channel.id)]
        )
        member_emp = members.filtered(
            lambda m: m.partner_id == self.user_emp.partner_id
        )
        member_publisher = members.filtered(
            lambda m: m.partner_id == self.user_officer.partner_id
        )

        slides_emp = (self.slide | self.slide_2).with_user(self.user_emp)
        slides_emp.action_set_viewed()
        self.assertEqual(member_emp.completed_time, 0)

        slides_emp.action_mark_completed()

        slides_emp_completed_time = sum(slides_emp.mapped("completion_time"))
        self.assertEqual(member_emp.completed_time, slides_emp_completed_time)
        self.slide_3.with_user(self.user_emp)._action_mark_completed()
        slides_emp_completed_time += self.slide_3.completion_time
        self.assertEqual(member_emp.completed_time, slides_emp_completed_time)

        # The following tests should update the completed_time even for users
        # that have already completed the course

        self.slide_3.is_published = False
        slides_emp_completed_time -= self.slide_3.completion_time
        self.assertEqual(member_emp.completed_time, slides_emp_completed_time)
        self.slide_3.is_published = True
        self.slide_3.active = False
        self.assertEqual(member_emp.completed_time, slides_emp_completed_time)

        # Should update completed_time when slide is marked as completed

        self.assertEqual(member_publisher.completed_time, 0)
        self.slide.with_user(self.user_officer).action_mark_completed()
        slides_publisher_completed_time = self.slide.completion_time
        self.assertEqual(
            member_publisher.completed_time, slides_publisher_completed_time
        )

        # Should update completed_time when slide is (un)archived
        self.slide_3.active = True
        slides_emp_completed_time += self.slide_3.completion_time
        self.assertEqual(member_emp.completed_time, slides_emp_completed_time)
        self.assertEqual(
            member_publisher.completed_time, slides_publisher_completed_time
        )

        # Shouln't update completed_time when a new published slide is created
        self.slide_4 = self.slide_3.copy({"is_published": True})
        self.assertEqual(member_emp.completed_time, slides_emp_completed_time)
        self.assertEqual(
            member_publisher.completed_time, slides_publisher_completed_time
        )

        # Shouldn't update completed_time when slide is (un)published
        self.slide_4.is_published = False
        self.assertEqual(member_emp.completed_time, slides_emp_completed_time)
        self.assertEqual(
            member_publisher.completed_time, slides_publisher_completed_time
        )

        # Should update completed_time when slide is marked as uncompleted
        self.slide.with_user(self.user_emp).action_mark_uncompleted()
        slides_emp_completed_time -= self.slide.completion_time
        self.assertEqual(member_emp.completed_time, slides_emp_completed_time)
        self.assertEqual(
            member_publisher.completed_time, slides_publisher_completed_time
        )

        # Should update completed_time when a slide is unlinked
        slides_publisher_completed_time -= self.slide.completion_time
        self.slide.with_user(self.user_manager).unlink()
        self.assertEqual(member_emp.completed_time, slides_emp_completed_time)
        self.assertEqual(
            member_publisher.completed_time, slides_publisher_completed_time
        )
