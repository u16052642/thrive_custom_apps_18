# -*- coding: utf-8 -*-
# from thrive import http


# class HrPayrollPdfReport(http.Controller):
#     @http.route('/hr_payroll_pdf_report/hr_payroll_pdf_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_payroll_pdf_report/hr_payroll_pdf_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_payroll_pdf_report.listing', {
#             'root': '/hr_payroll_pdf_report/hr_payroll_pdf_report',
#             'objects': http.request.env['hr_payroll_pdf_report.hr_payroll_pdf_report'].search([]),
#         })

#     @http.route('/hr_payroll_pdf_report/hr_payroll_pdf_report/objects/<model("hr_payroll_pdf_report.hr_payroll_pdf_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_payroll_pdf_report.object', {
#             'object': obj
#         })
