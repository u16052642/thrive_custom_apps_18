from thrive import api, fields, models, _


class ProjectWBSEntries(models.TransientModel):
    _name = 'wbs.entries'
    _description = "WBS Entries"

    boq_qty = fields.Float(string="BOQ Qty", default=1)
    activity_id = fields.Many2one('job.type', string="Work Type")
    sub_work_type_ids = fields.Many2many('job.sub.category', string="Work Type Jobs",
                                         compute="compute_sub_work_type_ids")
    sub_work_type_id = fields.Many2one('job.sub.category',
                                       string="Work Sub Type", domain="[('id','in',sub_work_type_ids)]")

    @api.model
    def default_get(self, fields):
        res = super(ProjectWBSEntries, self).default_get(fields)
        active_id = self._context.get('active_id')
        phase_id = self.env['job.costing'].browse(active_id)
        res['activity_id'] = phase_id.activity_id.id
        return res

    @api.depends('activity_id')
    def compute_sub_work_type_ids(self):
        active_id = self._context.get('active_id')
        phase_id = self.env['job.costing'].browse(active_id)
        ids = self.env['boq.budget'].sudo().search(
            [('project_id', '=', phase_id.project_id.id), ('activity_id', '=', self.activity_id.id)]).mapped(
            'sub_activity_id').mapped('id')
        work_type_ids = [x for x in ids if x not in phase_id.sub_work_type_ids.ids] + [x for x in
                                                                                       phase_id.sub_work_type_ids.ids if
                                                                                       x not in ids]
        self.sub_work_type_ids = work_type_ids

    def action_create_wbs_entries(self):
        active_id = self._context.get('active_id')
        phase_id = self.env['job.costing'].browse(active_id)
        domain = [('job_type_id', '=', self.activity_id.id), ('sub_category_id', '=', self.sub_work_type_id.id),
                  ('sub_project_budget_id', '=', phase_id.project_id.budget_id.id)]
        budget_record_id = self.env['project.budget'].search(domain, limit=1)
        if not budget_record_id:
            msg = "Budget Entry with work type " + str(self.activity_id.name) + " and sub work type " + str(
                self.sub_work_type_id.name) + " not found."
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('Not Found !'),
                    'message': msg,
                    'sticky': False,
                }
            }
            return message
        if budget_record_id:
            work_sub_type_ids = phase_id.sub_work_type_ids.ids
            work_sub_type_ids.append(self.sub_work_type_id.id)
            phase_id.write({'sub_work_type_ids': work_sub_type_ids})
            for data in budget_record_id.rate_analysis_id.material_analysis_ids:
                self.env['cost.material.line'].create({
                    'sub_category_id': self.sub_work_type_id.id,
                    'material_id': data.product_id.id,
                    'name': data.name,
                    'qty': data.qty * self.boq_qty,
                    'cost': data.price,
                    'tax_id': data.tax_id.id,
                    'boq_per_qty': data.qty,
                    'job_costing_id': phase_id.id
                })
            for data in budget_record_id.rate_analysis_id.equipment_analysis_ids:
                self.env['cost.equipment.line'].create({
                    'sub_category_id': self.sub_work_type_id.id,
                    'equipment_id': data.product_id.id,
                    'name': data.name,
                    'qty': data.qty * self.boq_qty,
                    'cost': data.price,
                    'tax_id': data.tax_id.id,
                    'boq_per_qty': data.qty,
                    'job_costing_id': phase_id.id
                })
            for data in budget_record_id.rate_analysis_id.labour_analysis_ids:
                self.env['cost.labour.line'].create({
                    'sub_category_id': self.sub_work_type_id.id,
                    'product_id': data.product_id.id,
                    'name': data.name,
                    'hours': data.qty * self.boq_qty,
                    'cost': data.price,
                    'tax_id': data.tax_id.id,
                    'boq_per_qty': data.qty,
                    'job_costing_id': phase_id.id
                })
            for data in budget_record_id.rate_analysis_id.overhead_analysis_ids:
                self.env['cost.overhead.line'].create({
                    'sub_category_id': self.sub_work_type_id.id,
                    'product_id': data.product_id.id,
                    'name': data.name,
                    'qty': data.qty * self.boq_qty,
                    'cost': data.price,
                    'tax_id': data.tax_id.id,
                    'boq_per_qty': data.qty,
                    'job_costing_id': phase_id.id
                })
