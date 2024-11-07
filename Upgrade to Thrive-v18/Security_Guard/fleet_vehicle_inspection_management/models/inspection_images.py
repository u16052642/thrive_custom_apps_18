# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""model to add inspection images"""
from thrive import fields, models


class InspectionImages(models.Model):
    """Model to add inspection images"""
    _name = 'inspection.images'
    _description = 'Inspection Images'

    name = fields.Char(String='Image Name', help='Image name')
    image = fields.Binary(string='Image', help='Inspection Image')
    inspection_id = fields.Many2one('inspection.request',
                                    help='Vehicle inspection',
                                    string='Vehicle inspection')
    service_log_id = fields.Many2one('vehicle.service.log',
                                     help='Service log',
                                     string='Service log')
