# -*- coding: utf-8 -*-
# Part of Thrive Bureau ERP. See LICENSE file for full copyright and licensing details.

from thrive import api, fields, models, tools,  _


class ResUsers(models.Model):
    _inherit = 'res.users'

    login = fields.Char(index=True)
