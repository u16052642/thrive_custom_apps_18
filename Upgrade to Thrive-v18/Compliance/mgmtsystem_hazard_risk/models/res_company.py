# Copyright (C) 2020 Guadaltech Soluciones Tecnológicas (<http://www.guadaltech.es>).
# Part of Thrive. See LICENSE file for full copyright and licensing details.

from thrive import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    risk_computation_id = fields.Many2one(
        "mgmtsystem.hazard.risk.computation", string="Risk Computation"
    )
