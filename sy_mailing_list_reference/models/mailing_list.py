# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailingList(models.Model):
    _inherit = "mailing.list"

    ref = fields.Char(
        string='Reference',
    )
