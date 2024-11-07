# -*- coding: utf-8 -*-
# Part of thrive. See LICENSE file for full copyright and licensing details.


from thrive import models
from thrive.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(IrHttp, self).session_info()
        result['ua_type'] = self.get_ua_type()
        return result


