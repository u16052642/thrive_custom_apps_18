# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, api, models, _
from thrive.exceptions import ValidationError


class ConstructionSite(models.Model):
    _name = 'tk.construction.site'
    _description = "Construction Project"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Title", tracking=True)
    start_date = fields.Date(string="Start Date", tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)
    status = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('complete', 'Complete')],
                              default='draft', tracking=True)
    con_project_id = fields.Many2one('tk.construction.project', string="Project", tracking=True)
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", tracking=True)

    # Address
    zip = fields.Char(string='Pin Code')
    street = fields.Char(string='Street1')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one("res.country.state", string='State', readonly=False, store=True,
                               domain="[('country_id', '=?', country_id)]")
    longitude = fields.Char(string="Longitude")
    latitude = fields.Char(string="Latitude")

    # One2Many
    stakeholder_ids = fields.One2many('stakeholder.line', 'site_id')
    site_image_ids = fields.One2many('site.images', 'site_id')
    site_dimension_ids = fields.One2many('site.dimension', 'site_id')
    document_permit_ids = fields.One2many('document.permit', 'site_id')
    construction_project_ids = fields.One2many('tk.construction.project', 'construction_site_id')
    boq_ids = fields.One2many('tk.construction.project', 'construction_site_id')

    # Count & Totals
    document_count = fields.Integer(string="Document Count", compute="_compute_count")
    project_count = fields.Integer(string="Project Count", compute="_compute_count")
    total_area = fields.Float(string="Total Area ", compute="_compute_total_area")

    # Create, Write, Unlink, Constrain
    @api.constrains('stakeholder_ids')
    def _check_stakeholder_stack(self):
        for record in self.stakeholder_ids:
            duplicates = self.stakeholder_ids.filtered(
                lambda r: r.id != record.id and r.stakeholder_id.id == record.stakeholder_id.id)
            if duplicates:
                raise ValidationError(_("Stakeholder already added !"))

    @api.constrains('stakeholder_ids')
    def _check_stakeholder_ids(self):
        percentage = 0.0
        for record in self.stakeholder_ids:
            percentage = percentage + record.percentage
        if percentage > 100:
            raise ValidationError(_("Percentage cannot exceed the limit of 100%."))

    # Compute
    def _compute_count(self):
        for rec in self:
            rec.document_count = self.env['site.documents'].search_count([('site_id', '=', rec.id)])
            rec.project_count = self.env['tk.construction.project'].search_count(
                [('construction_site_id', '=', rec.id)])

    @api.depends('site_dimension_ids')
    def _compute_total_area(self):
        for rec in self:
            total = 0.0
            if rec.site_dimension_ids:
                for data in rec.site_dimension_ids:
                    total = total + data.area
            rec.total_area = total

    # Smart Bottom
    def action_gmap_location(self):
        if self.longitude and self.latitude:
            longitude = self.longitude
            latitude = self.latitude
            http_url = 'https://maps.google.com/maps?q=loc:' + latitude + ',' + longitude
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': http_url,
            }
        else:
            raise ValidationError(_("! Enter Proper Longitude and Latitude Values"))

    def action_site_document(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents'),
            'res_model': 'site.documents',
            'domain': [('site_id', '=', self.id)],
            'context': {'default_site_id': self.id},
            'view_mode': 'tree',
            'target': 'current'
        }

    def action_view_project(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Project'),
            'res_model': 'tk.construction.project',
            'domain': [('construction_site_id', '=', self.id)],
            'context': {'default_construction_site_id': self.id},
            'view_mode': 'tree,form',
            'target': 'current'
        }

    # Button
    def action_site_complete(self):
        self.status = 'complete'

    def action_site_in_progress(self):
        self.status = 'in_progress'


# Stakeholder
class StakeholderLine(models.Model):
    _name = 'stakeholder.line'
    _description = "Stack Holder Line"
    _rec_name = 'stakeholder_id'

    site_id = fields.Many2one('tk.construction.site', string="Construction Project")
    stakeholder_id = fields.Many2one('res.partner', domain="[('stack_holder','=',True)]")
    percentage = fields.Float(string="Percentage")
    image_1920 = fields.Binary(related="stakeholder_id.image_1920")
    phone = fields.Char(related="stakeholder_id.phone", string="Phone")
    email = fields.Char(related="stakeholder_id.email", string="Email")


# Project Documents
class SiteDocuments(models.Model):
    _name = 'site.documents'
    _description = "Project Documents"
    _rec_name = 'document_type_id'

    document_type_id = fields.Many2one('site.document.type', string="Document Type")
    date = fields.Date(string="Date", default=fields.Date.today())
    site_id = fields.Many2one('tk.construction.site', string="Construction Project", ondelete='cascade')
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(string='File Name')


# Project Images
class SiteImages(models.Model):
    _name = 'site.images'
    _description = "Project Images"

    site_id = fields.Many2one('tk.construction.site', string="Construction Project", ondelete='cascade')
    name = fields.Char(string='Title')
    image = fields.Image(string='Images')


# Project Dimension
class SiteDimension(models.Model):
    _name = 'site.dimension'
    _description = "Project Dimension"
    _rec_name = "site_id"

    name = fields.Char(string="Title")
    site_id = fields.Many2one('tk.construction.site', string="Construction Project", ondelete='cascade')
    length = fields.Float(string="Length(m)")
    width = fields.Float(string="Width(m)")
    area = fields.Float(string="Area", compute="_compute_area")

    @api.depends('length', 'width')
    def _compute_area(self):
        for rec in self:
            area = 0.0
            if rec.length and rec.width:
                area = rec.length * rec.width
            rec.area = area


# Document Permit
class DocumentPermit(models.Model):
    _name = 'document.permit'
    _description = "Document Permit"
    _rec_name = 'document_type_id'

    document_type_id = fields.Many2one('site.document.type', string="Document Type")
    date = fields.Date(string="Date", default=fields.Date.today())
    site_id = fields.Many2one('tk.construction.site', string="Construction Project", ondelete='cascade')
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(string='File Name')
    status = fields.Selection([('a', 'Approve'), ('r', 'Reject')], string="Status")
    feedback = fields.Char(string="Feedback")
    submitted_by = fields.Many2one('res.users', string="Submitted by",
                                   default=lambda self: self.env.user and self.env.user.id or False)

    def action_approve(self):
        self.status = 'a'

    def action_reject(self):
        self.status = 'r'
