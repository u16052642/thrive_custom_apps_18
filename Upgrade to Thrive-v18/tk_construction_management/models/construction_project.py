# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import xlwt
import base64
from io import BytesIO
from thrive import fields, api, models, _
from thrive.exceptions import UserError, ValidationError


class ConstructionProject(models.Model):
    _name = 'tk.construction.project'
    _description = "Construction Project"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Title", tracking=True)
    start_date = fields.Date(string="Schedule Start Date", tracking=True)
    end_date = fields.Date(string="Schedule End Date", tracking=True)
    project_progress = fields.Float(
        related="budget_id.progress", string="Progress", tracking=True)
    construction_site_id = fields.Many2one(
        'tk.construction.site', string="Project ", tracking=True)
    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user and self.env.user.id or False,
                                     string="Created By")
    stage = fields.Selection([('draft', 'Draft'),
                              ('Planning', 'Planning'),
                              ('Procurement', 'Procurement'),
                              ('Construction', 'Construction'),
                              ('Handover', 'Handover')], string="Stage", default="draft", tracking=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string="Warehouse", tracking=True)
    code = fields.Char(string="Code", tracking=True)
    project_id = fields.Many2one(
        'project.project', string="Project", tracking=True)
    engineer_ids = fields.Many2many(
        'hr.employee', string="Engineers", tracking=True)

    # Department
    department_id = fields.Many2one(
        'construction.department', string="Department", tracking=True)
    department_manager_ids = fields.Many2many(
        related="department_id.manager_ids", string="Department Manager")
    manager_ids = fields.Many2many('res.users', string="Manager")
    department_user_ids = fields.Many2many(
        related="department_id.user_ids", string="Department Users")
    user_id = fields.Many2one('res.users', string="Responsible")

    # Address
    zip = fields.Char(string='Pin Code')
    street = fields.Char(string='Street1')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one(
        "res.country.state", string='State', readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")
    longitude = fields.Char(string="Longitude")
    latitude = fields.Char(string="Latitude")

    # BOQ Details
    is_use_measure = fields.Boolean(
        string="Is use of (LENGTH x WIDTH x HEIGHT ) ?")
    boq_budget_ids = fields.One2many(
        'boq.budget', 'project_id', string="Budget ")

    # Budget
    budget_id = fields.Many2one('sub.project.budget', string="Budget")

    # One2Many
    document_ids = fields.One2many(
        'project.documents', 'project_id', string="Documents")
    policy_ids = fields.One2many(
        'project.insurance', 'project_id', string="Insurance")
    expense_ids = fields.One2many(
        'extra.expense', 'project_id', string="Expense")
    phase_ids = fields.One2many('job.costing', 'project_id')

    # Count & Totals
    job_sheet_count = fields.Integer(
        string="Project Phase Count", compute="_compute_count")
    job_order_count = fields.Integer(
        string="Work Order Count", compute="_compute_count")
    mrq_count = fields.Integer(string="MRQ Count", compute="_compute_count")
    mrq_po_count = fields.Integer(
        string="MRQ PO Count", compute="_compute_count")
    jo_po_count = fields.Integer(
        string="JO PO Count", compute="_compute_count")
    inspection_task_count = fields.Integer(
        string="Inspection Task Count", compute="_compute_count")
    task_count = fields.Integer(string="Task Count", compute="_compute_count")
    budget_count = fields.Integer(
        string="Budget Count", compute="_compute_count")

    # Create, Write, Unlink, Constrain
    @api.model_create_multi
    def create(self, vals):
        res = super(ConstructionProject, self).create(vals)
        for rec in res:
            data = {
                'name': rec.name + "'s Project",
                'construction_project_id': rec.id,
                'company_id': self.env.company.id,
                'privacy_visibility': 'followers'
            }
            project_id = self.env['project.project'].create(data)
            rec.project_id = project_id.id
            task_stage = self.env['project.task.type'].sudo().search(
                [('active', '=', True), ('user_id', '=', False)])
            ids = []
            for data in task_stage:
                ids = data.project_ids.ids
                ids.append(project_id.id)
                data.project_ids = ids
        return res

    @api.constrains('boq_budget_ids')
    def _check_sub_activity(self):
        for rec in self:
            activity_counts = {}
            for activity in rec.boq_budget_ids:
                key = (activity.activity_id.id, activity.sub_activity_id.id)
                if key in activity_counts:
                    activity_counts[key] += 1
                else:
                    activity_counts[key] = 1
            duplicate = [pair for pair,
                         count in activity_counts.items() if count > 1]
            if duplicate:
                raise ValidationError(
                    "Duplicate work type and sub work type pair found.")

    @api.onchange('construction_site_id')
    def onchange_site_address(self):
        for rec in self:
            if rec.construction_site_id:
                rec.zip = rec.construction_site_id.zip
                rec.street = rec.construction_site_id.street
                rec.street2 = rec.construction_site_id.street2
                rec.city = rec.construction_site_id.city
                rec.state_id = rec.construction_site_id.state_id.id
                rec.country_id = rec.construction_site_id.country_id.id
                rec.start_date = rec.construction_site_id.start_date
                rec.end_date = rec.construction_site_id.end_date

    # Compute
    def _compute_count(self):
        for rec in self:
            rec.job_sheet_count = self.env['job.costing'].search_count(
                [('project_id', '=', rec.id)])
            rec.job_order_count = self.env['job.order'].search_count(
                [('project_id', '=', rec.id)])
            rec.mrq_count = self.env['material.requisition'].search_count(
                [('project_id', '=', rec.id)])
            rec.mrq_po_count = self.env['purchase.order'].search_count(
                [('project_id', '=', rec.id)])
            job_order_ids = self.env['job.order'].search(
                [('project_id', '=', self.id)]).mapped('id')
            po_ids = self.env['purchase.order'].search(
                [('job_order_id', 'in', job_order_ids)]).mapped('id')
            rec.jo_po_count = len(po_ids)
            rec.task_count = self.env['project.task'].search_count(
                [('con_project_id', '=', rec.id), ('is_inspection_task', '=', False)])
            rec.inspection_task_count = self.env['project.task'].search_count(
                [('con_project_id', '=', rec.id), ('is_inspection_task', '=', True)])
            rec.budget_count = self.env['project.budget'].search_count(
                [('sub_project_budget_id', '=', rec.budget_id.id)])

    # Smart Button
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
            raise ValidationError(
                _("! Enter Proper Longitude and Latitude Values"))

    def action_view_job_sheet(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Project Phase(WBS)'),
            'res_model': 'job.costing',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_job_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order'),
            'res_model': 'job.order',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_material_requisition(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Material Requisition'),
            'res_model': 'material.requisition',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_mrq_purchase_orders(self):
        ids = self.env['purchase.order'].search(
            [('project_id', '=', self.id)]).mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('MRQ Purchase Order'),
            'res_model': 'purchase.order',
            'domain': [('id', 'in', ids)],
            'context': {'create': False},
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_jo_purchase_orders(self):
        job_order_ids = self.env['job.order'].search(
            [('project_id', '=', self.id)]).mapped('id')
        po_ids = self.env['purchase.order'].search(
            [('job_order_id', 'in', job_order_ids)]).mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order PO'),
            'res_model': 'purchase.order',
            'domain': [('id', 'in', po_ids)],
            'context': {'create': False, 'group_by': 'purchase_order'},
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_project_task(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Task'),
            'res_model': 'project.task',
            'domain': [('con_project_id', '=', self.id), ('is_inspection_task', '=', False)],
            'context': {'default_con_project_id': self.id, 'default_project_id': self.project_id.id},
            'view_mode': 'kanban,tree,form',
            'target': 'current'
        }

    def action_view_project_task_inspection(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Inspection Task'),
            'res_model': 'project.task',
            'domain': [('con_project_id', '=', self.id), ('is_inspection_task', '=', True)],
            'context': {'default_con_project_id': self.id, 'default_project_id': self.project_id.id,
                        'default_is_inspection_task': True, 'default_priority': '1'},
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_budget(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Budget'),
            'res_model': 'project.budget',
            'domain': [('sub_project_budget_id', '=', self.budget_id.id)],
            'context': {'default_sub_project_budget_id': self.budget_id.id},
            'view_mode': 'tree,kanban,form',
            'target': 'current'
        }

    # Button
    def action_project_planning(self):
        self.stage = 'Planning'

    def action_stage_procurement(self):
        if not self.warehouse_id:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': "Please choose a warehouse to proceed to the next stage of construction process",
                    'sticky': False,
                }
            }
            return message
        if not self.budget_id:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': "Please create a budget to proceed to the next stage of construction process",
                    'sticky': False,
                }
            }
            return message

        self.stage = 'Procurement'

    def action_stage_construction(self):
        self.stage = 'Construction'

    def action_stage_handover(self):
        phase_completed = True
        phase_record = self.env['job.costing'].search(
            [('project_id', '=', self.id)])
        for data in phase_record:
            if data.status != 'complete':
                phase_completed = False
                break
        if not phase_completed:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': "Please complete all the phases related to this project to handover this project.",
                    'sticky': False,
                }
            }
            return message
        self.stage = 'Handover'

    def get_float_time(self, t):
        hour, minute = divmod(t, 1)
        minute *= 60
        result = '{}:{}'.format(int(hour), int(minute))
        return result

    def action_print_budget_excel_report(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet1 = workbook.add_sheet('Budget Details', cell_overwrite_ok=True)
        sheet1.show_grid = False
        sheet1.col(0).width = 400
        sheet1.col(3).width = 600
        sheet1.col(9).width = 600
        sheet1.row(4).height = 400
        sheet1.row(5).height = 200
        sheet1.row(6).height = 400
        sheet1.row(7).height = 200
        sheet1.row(8).height = 400
        sheet1.row(9).height = 200
        sheet1.row(10).height = 400
        sheet1.row(11).height = 200
        sheet1.row(12).height = 400
        sheet1.row(17).height = 400
        sheet1.col(12).width = 5000
        sheet1.col(13).width = 4000
        sheet1.col(14).width = 5000
        sheet1.col(15).width = 5000
        sheet1.col(16).width = 8000
        sheet1.col(17).width = 7000
        sheet1.col(18).width = 7000
        sheet1.col(19).width = 7000
        sheet1.col(20).width = 7000
        sheet1.col(21).width = 7000
        sheet1.col(22).width = 5000
        sheet1.row(14).height = 600
        border_squre = xlwt.Borders()
        border_squre.bottom = xlwt.Borders.HAIR
        border_squre.bottom_colour = xlwt.Style.colour_map["sea_green"]
        al = xlwt.Alignment()
        al.horz = xlwt.Alignment.HORZ_LEFT
        al.vert = xlwt.Alignment.VERT_CENTER
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'mm/dd/yyyy'
        date_format.font.name = "Century Gothic"
        date_format.borders = border_squre
        date_format.alignment = al
        date_format.font.colour_index = 0x36
        date_format.font.bold = 1
        sheet1.set_panes_frozen(True)
        sheet1.set_horz_split_pos(18)
        sheet1.remove_splits = True
        title = xlwt.easyxf(
            "font: height 350, name Century Gothic, bold on, color_index blue_gray;"
            " align: vert center, horz center;"
            "border: bottom thick, bottom_color sea_green;")
        values = xlwt.easyxf(
            "font:name Century Gothic, bold on, color_index blue_gray;"
            " align: vert center, horz left;"
            "border: bottom hair, bottom_color sea_green;")
        line_percentage_value = xlwt.easyxf(
            "font:name Century Gothic, bold on, color_index blue_gray;"
            " align: vert center, horz center;"
            "border: bottom hair, bottom_color blue_gray, right hair,right_color blue_gray;")
        line_values = xlwt.easyxf(
            "font:name Century Gothic;"
            " align: vert center, horz center;"
            "border: bottom hair, bottom_color blue_gray, right hair,right_color blue_gray,left hair,left_color blue_gray;")
        line_amount_values = xlwt.easyxf(
            "font:name Century Gothic;"
            " align: vert center, horz right;"
            "border: bottom hair, bottom_color blue_gray, right hair,right_color blue_gray,left hair,left_color blue_gray;")
        line_amount_sub_title = xlwt.easyxf(
            "font: height 185, name Century Gothic, bold on, color_index gray80; "
            "align: vert center, horz right; "
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")
        sub_title = xlwt.easyxf(
            "font: height 185, name Century Gothic, bold on, color_index gray80; "
            "align: vert center, horz center; "
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")
        # Budget Details
        budget_amount = str(self.budget_id.currency_id.symbol) + \
            " "+str(self.budget_id.total_budget_amount)
        utilization_amount = str(self.budget_id.currency_id.symbol) + " " + str(
            self.budget_id.utilization_amount)
        utilization_percentage = str(self.budget_id.progress) + " %"
        sheet1.write_merge(0, 2, 1, 11, "Budget Details", title)
        sheet1.write_merge(4, 4, 1, 2, "Project", sub_title)
        sheet1.write_merge(4, 4, 4, 5, self.construction_site_id.name, values)
        sheet1.write_merge(6, 6, 1, 2, "Sub Project", sub_title)
        sheet1.write_merge(6, 6, 4, 5, self.name, values)
        sheet1.write_merge(4, 4, 7, 8, "Start Date", sub_title)
        sheet1.write_merge(
            4, 4, 10, 11, self.budget_id.start_date, date_format)
        sheet1.write_merge(6, 6, 7, 8, "End Date", sub_title)
        sheet1.write_merge(6, 6, 10, 11, self.budget_id.end_date, date_format)
        sheet1.write_merge(8, 8, 1, 2, "Total Budget Amount", sub_title)
        sheet1.write_merge(8, 8, 4, 5, budget_amount, values)
        sheet1.write_merge(10, 10, 1, 2, "Budget Utilization", sub_title)
        sheet1.write_merge(10, 10, 4, 5, utilization_amount, values)
        sheet1.write_merge(12, 12, 1, 2, "Utilization(%)", sub_title)
        sheet1.write_merge(12, 12, 4, 5, utilization_percentage, values)
        # Budget Lines
        sheet1.write_merge(14, 15, 1, 22, "Budget Lines", title)
        sheet1.write_merge(17, 17, 1, 3, "Work Type", sub_title)
        sheet1.write_merge(17, 17, 4, 6, "Work Sub Type", sub_title)
        sheet1.write(17, 7, "BOQ Qty", line_amount_sub_title)
        sheet1.write_merge(17, 17, 8, 10, "Additional Qty",
                           line_amount_sub_title)
        sheet1.write(17, 11, "Total Qty", line_amount_sub_title)
        sheet1.write(17, 12, "Rate Analysis", sub_title)
        sheet1.write(17, 13, "Price / Qty", line_amount_sub_title)
        sheet1.write(17, 14, "Untaxed", line_amount_sub_title)
        sheet1.write(17, 15, "Tax Amount", line_amount_sub_title)
        sheet1.write(17, 16, "Total Budget", line_amount_sub_title)
        sheet1.write(17, 17, "Material Spent", line_amount_sub_title)
        sheet1.write(17, 18, "Equipment Spent", line_amount_sub_title)
        sheet1.write(17, 19, "Labour Spent", line_amount_sub_title)
        sheet1.write(17, 20, "Overhead Spent", line_amount_sub_title)
        sheet1.write(17, 21, "Remaining Budget", line_amount_sub_title)
        sheet1.write(17, 22, "Utilization(%)", sub_title)
        col = 18
        for data in self.budget_id.budget_line_ids:
            sheet1.row(col).height = 400
            sheet1.write_merge(
                col, col, 1, 3, data.job_type_id.name, line_values)
            sheet1.write_merge(
                col, col, 4, 6, data.sub_category_id.name, line_values)
            sheet1.write(col, 7, data.boq_qty, line_amount_values)
            sheet1.write_merge(
                col, col, 8, 10, data.additional_qty, line_amount_values)
            sheet1.write(col, 11, (data.boq_qty +
                         data.additional_qty), line_amount_values)
            sheet1.write(col, 12, ((data.rate_analysis_id.name)
                         if data.rate_analysis_id else ""), line_values)
            sheet1.write(col, 13, (str(self.budget_id.currency_id.symbol) +
                         " " + str(data.price_per_qty)), line_amount_values)
            sheet1.write(col, 14, (str(self.budget_id.currency_id.symbol) +
                         " " + str(data.untaxed_amount)), line_amount_values)
            sheet1.write(col, 15, (str(self.budget_id.currency_id.symbol) +
                         " " + str(data.tax_amount)), line_amount_values)
            sheet1.write(col, 16, (str(self.budget_id.currency_id.symbol) +
                         " " + str(data.budget)), line_amount_values)
            sheet1.write(col, 17, (str(self.budget_id.currency_id.symbol) +
                         " " + str(data.material_spent)), line_amount_values)
            sheet1.write(col, 18, (str(self.budget_id.currency_id.symbol) +
                         " " + str(data.equipment_spent)), line_amount_values)
            sheet1.write(col, 19, (str(self.budget_id.currency_id.symbol) +
                         " " + str(data.labour_spent)), line_amount_values)
            sheet1.write(col, 20, (str(self.budget_id.currency_id.symbol) +
                         " " + str(data.overhead_spent)), line_amount_values)
            sheet1.write(col, 21, (str(self.budget_id.currency_id.symbol) +
                         " " + str(data.remaining_budget)), line_amount_values)
            sheet1.write(
                col, 22, (str(data.total_spent) + " " + "%"), line_percentage_value)
            col = col + 1

        # Budget Spent
        self.get_budget_spent(workbook=workbook)

        # Print Report
        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())
        attachment = self.env['ir.attachment'].sudo()
        filename = 'Budget Report' + ".xls"
        attachment_id = attachment.create(
            {'name': filename,
                'type': 'binary',
                'public': False,
                'datas': out})
        if attachment_id:
            report = {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % (attachment_id.id),
                'target': 'self',
            }
            return report

    def get_budget_spent(self, workbook):
        title = xlwt.easyxf(
            "font: height 300, name Century Gothic, bold on, color_index blue_gray;"
            " align: vert center, horz center;"
            "border: bottom thick, bottom_color sea_green;")
        title2 = xlwt.easyxf(
            "font: height 250, name Century Gothic, bold on, color_index blue_gray;"
            " align: vert center, horz left;"
            "border: bottom thin, bottom_color sea_green;")
        title3 = xlwt.easyxf(
            "font: height 250, name Century Gothic, bold on;"
            " align: vert center, horz right;"
            "border: bottom thin, bottom_color sea_green;")
        line_amount_sub_title = xlwt.easyxf(
            "font: height 185, name Century Gothic, bold on, color_index gray80; "
            "align: vert center, horz right; "
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")
        line_values = xlwt.easyxf(
            "font:name Century Gothic;"
            " align: vert center, horz center;"
            "border: bottom hair, bottom_color blue_gray, right hair,right_color blue_gray,left hair,left_color blue_gray;")
        sub_title = xlwt.easyxf(
            "font: height 185, name Century Gothic, bold on, color_index gray80; "
            "align: vert center, horz center; "
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")
        sub_title2 = xlwt.easyxf(
            "font: height 200, name Century Gothic, bold on, color_index gray80; "
            "align: vert center, horz left; "
            "border: bottom hair,"
            "bottom_color sea_green;")
        sub_title_amount = xlwt.easyxf(
            "font: height 200, name Century Gothic, bold on, color_index gray80; "
            "align: vert center, horz right; "
            "border: bottom hair,"
            "bottom_color sea_green;")
        horiz_double_line = xlwt.easyxf("border: top double, top_color gray50")
        for data in self.budget_id.budget_line_ids:
            budget_phase_ids = self.env['job.costing'].search(
                [('project_id', '=', self.id), ('activity_id', '=', data.job_type_id.id)]).mapped('id')
            domain = [('project_id', '=', self.id), ('work_type_id', '=', data.job_type_id.id),
                      ('sub_category_id', '=',
                       data.sub_category_id.id), ('state', '=', 'complete'),
                      ('job_sheet_id', 'in', budget_phase_ids)]
            material_spent_rec = self.env['order.material.line'].search(domain)
            equip_spent_rec = self.env['order.equipment.line'].search(domain)
            labour_spent_rec = self.env['order.labour.line'].search(domain)
            overhead_spent_rec = self.env['order.overhead.line'].search(domain)
            sheet_name = data.job_type_id.name + \
                "(" + data.sub_category_id.name + ")"
            sheet = workbook.add_sheet(sheet_name, cell_overwrite_ok=True)
            sheet.show_grid = False
            row = 0
            sheet.row(4).height = 400
            sheet.row(6).height = 400
            sheet.write_merge(0, 2, 0, 6, sheet_name, title)
            sheet.write(4, 0, "Total Budget", sub_title2)
            sheet.write(4, 1, (str(self.budget_id.currency_id.symbol) +
                               " " + str(data.budget)), sub_title_amount)
            sheet.write_merge(4, 4, 3, 4, "Used Budget Amount", sub_title2)
            sheet.write_merge(4, 4, 5, 6, (str(self.budget_id.currency_id.symbol) +
                                           " " + str((data.budget - data.remaining_budget))), sub_title_amount)
            sheet.write_merge(6, 6, 3, 4, "Remaining Budget", sub_title2)
            sheet.write_merge(6, 6, 5, 6, (str(self.budget_id.currency_id.symbol) +
                                           " " + str(data.remaining_budget)), sub_title_amount)
            row = 5
            # Material Rec
            sheet.write_merge(row+4, row+5, 0, 4, "Material Spent", title2)
            sheet.write_merge(row+4, row+5, 5, 6, (str(self.budget_id.currency_id.symbol) +
                                                   " " + str(data.material_spent)), title3)
            sheet.col(0).width = 8000
            sheet.col(1).width = 8000
            sheet.col(2).width = 6500
            sheet.col(3).width = 5000
            sheet.col(4).width = 5000
            sheet.col(5).width = 5000
            sheet.col(6).width = 5000
            sheet.row(row+6).height = 600
            sheet.write(row+6, 0, "Project Phase(WBS)", sub_title)
            sheet.write(row+6, 1, "Work Order", sub_title)
            sheet.write(row+6, 2, "Material", sub_title)
            sheet.write(row+6, 3, "Qty.", line_amount_sub_title)
            sheet.write(row+6, 4, "Unit", sub_title)
            sheet.write(row+6, 5, "Price/Qty", line_amount_sub_title)
            sheet.write(row+6, 6, "Total Price", line_amount_sub_title)
            row = row + 7
            for rec in material_spent_rec:
                sheet.row(row).height = 400
                sheet.write(row, 0, (rec.job_sheet_id.name +
                            " - " + rec.job_order_id.name), line_values)
                sheet.write(row, 1, (rec.job_order_id.name +
                            " - " + rec.job_order_id.name), line_values)
                sheet.write(row, 2, rec.name, line_values)
                sheet.write(row, 3, rec.qty, line_amount_sub_title)
                sheet.write(row, 4, rec.uom_id.name, line_values)
                sheet.write(row, 5, (str(self.budget_id.currency_id.symbol) +
                                     " " + str(rec.price)), line_amount_sub_title)
                sheet.write(row, 6, (str(self.budget_id.currency_id.symbol) +
                                     " " + str(rec.total_price)), line_amount_sub_title)
                row = row + 1
            sheet.write_merge(row, row, 0, 6, " ", horiz_double_line)
            row = row + 1

            # Equipment Rec
            sheet.write_merge(row+1, row+2, 0, 4, "Equipment Spent", title2)
            sheet.write_merge(row+1, row+2, 5, 6, (str(self.budget_id.currency_id.symbol) +
                                                   " " + str(data.equipment_spent)), title3)
            row = row + 3
            sheet.row(row).height = 600
            sheet.write(row, 0, "Project Phase(WBS)", sub_title)
            sheet.write(row, 1, "Work Order", sub_title)
            sheet.write(row, 2, "Vendor", sub_title)
            sheet.write(row, 3, "Equipment.", sub_title)
            sheet.write(row, 4, "Qty.", line_amount_sub_title)
            sheet.write(row, 5, "Price/Qty", line_amount_sub_title)
            sheet.write(row, 6, "Total Price", line_amount_sub_title)
            row = row+1
            for rec in equip_spent_rec:
                sheet.row(row).height = 400
                sheet.write(row, 0, (rec.job_sheet_id.name +
                            " - " + rec.job_order_id.name), line_values)
                sheet.write(row, 1, (rec.job_order_id.name +
                            " - " + rec.job_order_id.name), line_values)
                sheet.write(row, 2, rec.vendor_id.name, line_values)
                sheet.write(row, 3, rec.desc, line_values)
                sheet.write(row, 4, rec.qty, line_amount_sub_title)
                sheet.write(row, 5, (str(self.budget_id.currency_id.symbol) +
                                     " " + str(rec.cost)), line_amount_sub_title)
                sheet.write(row, 6, (str(self.budget_id.currency_id.symbol) +
                                     " " + str(rec.total_cost)), line_amount_sub_title)
                row = row + 1
            sheet.write_merge(row, row, 0, 6, " ", horiz_double_line)
            row = row + 1

            # Labour Rec
            sheet.write_merge(row+1, row+2, 0, 4, "Labour Spent", title2)
            sheet.write_merge(row+1, row+2, 5, 6, (str(self.budget_id.currency_id.symbol) +
                                                   " " + str(data.labour_spent)), title3)
            row = row + 3
            sheet.row(row).height = 600
            sheet.write(row, 0, "Project Phase(WBS)", sub_title)
            sheet.write(row, 1, "Work Order", sub_title)
            sheet.write(row, 2, "Vendor", sub_title)
            sheet.write(row, 3, "Product", sub_title)
            sheet.write(row, 4, "Hours", line_amount_sub_title)
            sheet.write(row, 5, "Cost / Hour", line_amount_sub_title)
            sheet.write(row, 6, "Sub Total", line_amount_sub_title)
            row = row+1
            for rec in labour_spent_rec:
                sheet.row(row).height = 400
                sheet.write(row, 0, (rec.job_sheet_id.name +
                            " - " + rec.job_order_id.name), line_values)
                sheet.write(row, 1, (rec.job_order_id.name +
                            " - " + rec.job_order_id.name), line_values)
                sheet.write(row, 2, rec.vendor_id.name, line_values)
                sheet.write(row, 3, rec.name, line_values)
                sheet.write(row, 4, rec.hours, line_amount_sub_title)
                sheet.write(row, 5, (str(self.budget_id.currency_id.symbol) +
                                     " " + str(rec.cost)), line_amount_sub_title)
                sheet.write(row, 6, (str(self.budget_id.currency_id.symbol) +
                                     " " + str(rec.sub_total)), line_amount_sub_title)
                row = row + 1
            sheet.write_merge(row, row, 0, 6, " ", horiz_double_line)
            row = row + 1

            # Overhead Rec
            sheet.write_merge(row+1, row+2, 0, 4, "Overhead Spent", title2)
            sheet.write_merge(row+1, row+2, 5, 6, (str(self.budget_id.currency_id.symbol) +
                                                   " " + str(data.overhead_spent)), title3)
            row = row + 3
            sheet.row(row).height = 600
            sheet.write(row, 0, "Project Phase(WBS)", sub_title)
            sheet.write(row, 1, "Work Order", sub_title)
            sheet.write(row, 2, "Vendor", sub_title)
            sheet.write(row, 3, "Product", sub_title)
            sheet.write(row, 4, "Qty.", line_amount_sub_title)
            sheet.write(row, 5, "Cost / Qty", line_amount_sub_title)
            sheet.write(row, 6, "Sub Total", line_amount_sub_title)
            row = row+1
            for rec in overhead_spent_rec:
                sheet.row(row).height = 400
                sheet.write(row, 0, (rec.job_sheet_id.name +
                            " - " + rec.job_order_id.name), line_values)
                sheet.write(row, 1, (rec.job_order_id.name +
                            " - " + rec.job_order_id.name), line_values)
                sheet.write(row, 2, rec.vendor_id.name, line_values)
                sheet.write(row, 3, rec.name, line_values)
                sheet.write(row, 4, rec.qty, line_amount_sub_title)
                sheet.write(row, 5, (str(self.budget_id.currency_id.symbol) +
                                     " " + str(rec.cost)), line_amount_sub_title)
                sheet.write(row, 6, (str(self.budget_id.currency_id.symbol) +
                                     " " + str(rec.sub_total)), line_amount_sub_title)
                row = row + 1
            sheet.write_merge(row, row, 0, 6, " ", horiz_double_line)
            row = row + 1


class ProjectDocuments(models.Model):
    _name = 'project.documents'
    _description = "Project Documents"
    _rec_name = 'file_name'

    document_type_id = fields.Many2one('site.document.type', string="Document")
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(string='File Name')
    project_id = fields.Many2one('tk.construction.project')


class ProjectInsurance(models.Model):
    _name = 'project.insurance'
    _description = "Project Insurance"

    name = fields.Char(string="Insurance")
    policy_no = fields.Char(string="Insurance No")
    risk_ids = fields.Many2many('insurance.risk', string="Risk Covered")
    document = fields.Binary(string='Documents')
    file_name = fields.Char(string='File Name')
    project_id = fields.Many2one('tk.construction.project')
    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    total_charge = fields.Monetary(string="Total Charge")
    issue_date = fields.Date(string="Issue Date", default=fields.Date.today())
    bill_id = fields.Many2one('account.move', string="Bill")
    vendor_id = fields.Many2one('res.partner', string="Vendor")

    def action_create_bil(self):
        record = {
            'product_id': self.env.ref('tk_construction_management.construction_product_1').id,
            'name': self.project_id.name + "\n" + "Name : " + self.name + "\n" + "No : " + self.policy_no,
            'quantity': 1,
            'tax_ids': False,
            'price_unit': self.total_charge
        }
        line = [(0, 0, record)]
        main_data = {
            'partner_id': self.vendor_id.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.date.today(),
            'invoice_line_ids': line,
        }
        bill_id = self.env['account.move'].create(main_data)
        self.bill_id = bill_id.id


class ConstructionExtraExpense(models.Model):
    _name = 'extra.expense'
    _description = "Extra Expense"

    product_id = fields.Many2one(
        'product.product', string="Expense", domain="[('is_expense','=',True)]")
    date = fields.Date(string="Date", default=fields.Date.today())
    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    cost = fields.Monetary(string="Cost")
    bill_id = fields.Many2one('account.move', string="Bill")
    note = fields.Char(string="Note")
    project_id = fields.Many2one('tk.construction.project', string="Project")
    qty = fields.Integer(string="Qty.", default=1)
    vendor_id = fields.Many2one('res.partner', string="Vendor")

    def action_create_expense_bill(self):
        if self.vendor_id and self.product_id:
            data = {
                'product_id': self.product_id.id,
                'name': (self.product_id.name + " " + self.note) if self.note else self.product_id.name,
                'quantity': self.qty,
                'tax_ids': False,
                'price_unit': self.cost
            }
            invoice_line = [(0, 0, data)]
            invoice_id = self.env['account.move'].create({
                'partner_id': self.vendor_id.id,
                'invoice_line_ids': invoice_line,
                'move_type': 'in_invoice',
            })
            self.bill_id = invoice_id.id

    @api.onchange('product_id')
    def onchange_expense_cost(self):
        for rec in self:
            rec.cost = rec.product_id.standard_price


class BoqBudget(models.Model):
    _name = 'boq.budget'
    _description = "Boq Budget"
    _rec_name = 'activity_id'

    project_id = fields.Many2one(
        'tk.construction.project', string="Sub Project")
    site_id = fields.Many2one(
        related="project_id.construction_site_id", string="Project")
    activity_id = fields.Many2one('job.type', string="Work Type")
    sub_activity_ids = fields.Many2many(
        related="activity_id.sub_category_ids", string="Sub Activities")
    sub_activity_id = fields.Many2one('job.sub.category', string="Work Sub Type",
                                      domain="[('id','in',sub_activity_ids)]")
    qty = fields.Float(string="Qty.", default=1.0)
    total_qty = fields.Float(
        string="Total Qty.", compute="compute_total_qty", store=True)
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    height = fields.Float(string="Height")
    is_use_measure = fields.Boolean(
        related="project_id.is_use_measure", store=True)

    @api.depends('project_id.is_use_measure', 'length', 'width', 'height', 'qty')
    def compute_total_qty(self):
        for rec in self:
            total_qty = 0.0
            if rec.project_id.is_use_measure:
                total_qty = rec.height * rec.width * rec.length * rec.qty
            else:
                total_qty = rec.qty
            rec.total_qty = total_qty
