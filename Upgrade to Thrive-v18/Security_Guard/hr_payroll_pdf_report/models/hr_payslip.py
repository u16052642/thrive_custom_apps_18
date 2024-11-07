from thrive import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'hr payroll pdf report download'

    def action_print_employee_payslip(self):
        # datas = {'active_ids': self.id,
        #          'object':self,'name':'Payslip - '+self.employee_id.name + ' - '+self.number}
        return self.env.ref('hr_payroll_pdf_report.action_custom_employee_report_payslip').report_action(self)
