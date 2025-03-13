This module links sales order lines to `slide.channel.partner` participations when
selling a course. It does not add new views or user interface elements but ensures
that when a course is sold through Odoo's eLearning system, the corresponding sales
order line is associated with the participation record.

This functionality is useful for:

- Tracking which sale order line is responsible for a given course participation.
- Ensuring better traceability between sales and enrollments.
- Serving as a base for other modules that may extend its logic.
