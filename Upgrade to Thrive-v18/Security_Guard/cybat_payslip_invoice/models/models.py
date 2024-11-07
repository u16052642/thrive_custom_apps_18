# -*- coding: utf-8 -*-
from datetime import datetime, time

from thrive import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    run_id = fields.Many2one('hr.payslip.run')

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    project_id = fields.Many2one('project.project')
    invoice_count = fields.Integer(compute='get_invoice_count')

    def get_invoice_count(self):
        self.invoice_count = self.env['account.move'].search_count([('run_id','=',self.id)])
    def create_invoice(self):
        total = sum(self.slip_ids.mapped('net_wage'))
        if total:
            lines_vals = []
            product_id = self.env['product.template'].search([('name', '=', 'Timesheet Charges')], limit=1)
            if not product_id:
                product_id = self.env['product.template'].create({
                    'name': 'Timesheet Charges',
                    'type': 'service'
                })
            lines_vals.append((0, 0,
                               {'product_id': product_id.id,
                                'quantity': 1,
                                'price_unit': sum(self.slip_ids.mapped('net_wage')),
                                'tax_ids': False}
                               ))
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'invoice_date':fields.date.today(),
                'partner_id': self.project_id.partner_id.id,
                'invoice_line_ids': lines_vals,
                'run_id':self.id

            })

    def action_open_invoices(self):

        return {
            'name': ('Invoices'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('run_id', '=', self.id)],
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
