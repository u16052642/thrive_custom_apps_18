# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
# Developed by Bizople Solutions Pvt. Ltd.

from thrive.modules.module import get_resource_path
from thrive import api, http, fields, models, tools, _
from thrive.http import request
import base64

class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    tab_name = fields.Char(related='company_id.tab_name',
                           string="Backend Tab Name", readonly=False)
    backend_theme_level = fields.Selection(
        related='company_id.backend_theme_level', string="Backend Theme Level", required=True, readonly=False)
    
    login_page_style = fields.Selection(
        related='company_id.login_page_style', string="Login Styles", required=True, readonly=False)

    login_page_background_img = fields.Binary(
        related='company_id.login_page_background_img', string="Login Background Image", readonly=False)
    
    login_page_background_color = fields.Char(
        related='company_id.login_page_background_color', string='Login Background Color', readonly=False)
    
    login_page_text_color = fields.Char(
        related='company_id.login_page_text_color', string='Login Text Color', readonly=False)
    
    show_bg_image = fields.Boolean(
        related='company_id.show_bg_image', string='Add Login Background Image', readonly=False)
    spiffy_favicon = fields.Binary(
        related='company_id.spiffy_favicon', string="Backend Tab Favicon", readonly=False)
    backend_menubar_logo = fields.Binary(
        related='company_id.backend_menubar_logo', string="Menubar Logo", readonly=False)
    
    backend_menubar_logo_icon = fields.Binary(
        related='company_id.backend_menubar_logo_icon', string="Menubar Logo Icon", readonly=False)

    # Fields for PWA start
    enable_pwa = fields.Boolean(
        string='Enable PWA', related='company_id.enable_pwa', readonly=False,)
    app_name_pwa = fields.Char(
        'App Name', related='company_id.app_name_pwa', readonly=False)
    short_name_pwa = fields.Char(
        'Short Name', related='company_id.short_name_pwa', readonly=False)
    description_pwa = fields.Char(
        'App Description', related='company_id.description_pwa', readonly=False)
    image_192_pwa = fields.Binary(
        'Image 192px', related='company_id.image_192_pwa', readonly=False)
    image_512_pwa = fields.Binary(
        'Image 512px', related='company_id.image_512_pwa', readonly=False)
    start_url_pwa = fields.Char(
        'App Start Url', related='company_id.start_url_pwa', readonly=False)
    background_color_pwa = fields.Char(
        'Background Color', related='company_id.background_color_pwa', readonly=False)
    theme_color_pwa = fields.Char(
        'Theme Color', related='company_id.theme_color_pwa', readonly=False)
    pwa_shortcuts_ids = fields.Many2many(
        related='company_id.pwa_shortcuts_ids', readonly=False)
    # Fields for PWA end

    spiffy_toobar_color = fields.Char('Toolbar Color', related='company_id.spiffy_toobar_color', readonly=False)

    prevent_auto_save = fields.Boolean(
        related='company_id.prevent_auto_save', string='Prevent Auto Save ?', readonly=False)

    prevent_auto_save_warning = fields.Char('Auto Save Warning', related='company_id.prevent_auto_save_warning', readonly=False)
    
    firebase_server_key = fields.Char(string='Firebase key', related='company_id.firebase_server_key', readonly=False)
    
    def set_values(self):
        res = super(ResConfig, self).set_values()
        config_parameters = self.env['ir.config_parameter']
        config_parameters.set_param(
            "firebase_server_key", self.firebase_server_key)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfig, self).get_values()
        firebase_server_key=self.env['ir.config_parameter'].get_param('firebase_server_key')
        if not firebase_server_key:
            firebase_server_key = "AAAAl184GwM:APA91bEm2nxRGsz0GMeV7TDQ1OjwzKKkjmPOxTJLEFy3LaE7iowj3JN8WcNAuGcdDVDcwJpnkp-T5Uy0B_4dN6ytRN77F1CV_u10JdV9phduFe_qrORu_3FRmo2g33__mVBZH9yEFwhC"
        res.update(firebase_server_key=firebase_server_key)
        return res