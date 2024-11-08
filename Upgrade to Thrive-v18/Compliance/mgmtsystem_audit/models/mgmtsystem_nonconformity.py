# Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from thrive import fields, models


class MgmtsystemNonconformity(models.Model):
    """Class use to add audit_ids association to MgmtsystemNonconformity."""

    _inherit = "mgmtsystem.nonconformity"

    audit_ids = fields.Many2many("mgmtsystem.audit", string="Related Audits")
