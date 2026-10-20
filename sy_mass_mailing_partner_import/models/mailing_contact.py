# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailingContact(models.Model):
    _inherit = "mailing.contact"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("email", "!=", False)],
        index=True,
        ondelete="set null",
    )
    partner_ref = fields.Char(
        string="Partner Reference",
        related="partner_id.ref",
        store=True,
        index=True,
    )

    _sql_constraints = [  # noqa: RUF012
        (
            "partner_id_unique",
            "UNIQUE(partner_id)",
            "A partner can only be linked to one mailing contact.",
        ),
    ]
