# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import api, fields, models


class ConstructionResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    phase_prefix = fields.Char(string='Phase Prefix', default="PHASE/",
                               config_parameter='tk_construction_management.phase_prefix')
