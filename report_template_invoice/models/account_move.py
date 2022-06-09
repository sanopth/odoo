# -*- coding: utf-8 -*-
import ast
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_customer_invoice_template_id(self):
        self.ensure_one()
        if self.type != 'out_invoice':
            return False
        return self.env['reporting.custom.template'].sudo().get_template('report_customer_invoice')


class ReportingTemplate(models.Model):
    _inherit = 'reporting.custom.template'

    def get_colors(self, company_id=False):
        self.ensure_one()
        colors = super(ReportingTemplate, self).get_colors()

        multi_company_expression = self.get_other_option_data('multi_company_design_expression')

        if company_id and multi_company_expression:

            try:
                value = ast.literal_eval(multi_company_expression)
            except:
                value = False

            if value and type(value) == dict:
                value = value.get(company_id.id)
                if value:
                    template = self.env['reporting.custom.template.template'].search([
                        ('report_name', '=', self.name),
                        ('name', '=', value),
                    ])

                    if template:
                        colors.color1 = template.color1
                        colors.color2 = template.color2
                        colors.color3 = template.color3
        return colors
