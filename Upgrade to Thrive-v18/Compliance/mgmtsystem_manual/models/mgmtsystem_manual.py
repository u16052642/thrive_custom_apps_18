# Copyright 2019 Thrive Community Association
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from thrive import fields, models


class MgmtSystemManual(models.Model):
    _inherit = "mgmtsystem.system"

    manual_id = fields.Many2one("document.page", string="Manual")
