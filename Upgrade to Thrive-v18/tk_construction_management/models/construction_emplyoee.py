# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import api, fields, models


class ConstructionEmployee(models.Model):
    _inherit = "hr.employee"
