# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, api, models


class ConstructionPartner(models.Model):
    _inherit = 'res.partner'

    stack_holder = fields.Boolean(string="Stockholder")
