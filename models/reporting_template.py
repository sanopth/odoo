# -*- coding: utf-8 -*-
import ast
from odoo import models, fields

SEPARATORS = [
    ('next_line', 'Next Line'),
    ('comma', 'Comma'),
]

ALIGNMENT_VALS = [
    ('left', 'Left'),
    ('center', 'Center'),
    ('right', 'Right'),
]

DATE_FORMATS = [
    ("01_%d %b %Y", "18 Feb 2020"),
    ("02_%d/%b/%Y", "18/Feb/2020"),
    ("03_%d %B %Y", "18 February 2020"),
    ("04_%d/%m/%Y", "18/02/2020"),
    ("05_%d/%m/%y", "18/02/20"),
    ("06_%m/%d/%Y", "02/18/2020"),
    ("07_%d-%b-%Y", "18-Feb-2020"),
    ("08_%d. %b. %Y", "18.Feb. 2020"),
    ("09_%b %d, %y", "Feb 18, 20"),
    ("10_%B %d, %y", "February 18, 20"),
    ("11_%b %d, %Y", "Feb 18, 2020"),
    ("12_%B %d, %Y", "February 18, 2020"),
    ("13_%A, %d %b %Y", "Tuesday, 18 Feb 2020"),
    ("14_%A, %B %d, %Y", "Tuesday, February 18, 2020"),
    ("15_%a, %B %d, %Y", "Tue, February 18, 2020"),
    ("16_%a, %B %d, %y", "Tue, February 18, 20"),
    ("17_%a, %b %d, %Y", "Tue, Feb 18, 2020"),
    ("18_%a, %b %d, %y", "Tue, Feb 18, 20"),
]


def float_range(start, stop, step=1.0):
    result = []
    count = start
    while count <= stop:
        result.append(round(count, 2))
        count += step
    return result


class ColorObject:

    color1 = False
    color2 = False
    color3 = False

    def __init__(self, a=None, b=None, c=None):
        self.color1 = a
        self.color2 = b
        self.color3 = c


class Font:
    size = False
    family = False

    def __init__(self, size="16px"):
        self.size = size
        self.family = "none"

    @staticmethod
    def convert_size_to_int(size):
        result = ast.literal_eval(size.replace("px", ""))
        return int(result)

    @staticmethod
    def convert_int_to_size(num):
        return str(num) + "px"

    def get_size(self, percent=None):
        size_int = self.convert_size_to_int(self.size)

        if percent:
            result = size_int * percent / 100
            return self.convert_int_to_size(round(result))


def getattr_new(obj, attribute):
    o = obj
    for each in attribute.split('.'):
        o = getattr(o, each)
    return o


def add_thousands_separator(num):
    return '{:,.2f}'.format(num)


def rchop(s, suffix):
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def get_all_font_list(with_extension=False):
    vals = []
    import os
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(dir_path) + '/static/fonts'
    for each in os.listdir(dir_path):
        if each.endswith('ttf'):
            font = each
            if not with_extension:
                font = rchop(font, ".ttf")
            vals.append((font, font))
    return sorted(vals)


FONT_LIST = get_all_font_list()


class ReportingTemplate(models.Model):
    _name = 'reporting.custom.template'
    _rec_name = 'name_display'

    name = fields.Char(required=True, string='Technical Name')
    name_display = fields.Char(required=True, string='Report Name')
    model_id = fields.Many2one('ir.model')
    line_model_id = fields.Many2one('ir.model')
    template_id = fields.Many2one('reporting.custom.template.template')
    template_preview = fields.Binary(related='template_id.image', readonly=True)
    header_company_field_ids = fields.One2many('reporting.custom.template.header.field', 'report_id')
    footer_company_field_ids = fields.One2many('reporting.custom.template.footer.field', 'report_id')
    visible_partner_section = fields.Boolean(default=False)
    partner_field_ids = fields.One2many('reporting.custom.template.partner.field', 'report_id')
    visible_section_2 = fields.Boolean(default=False)
    section_2_field_ids = fields.One2many('reporting.custom.template.section.2', 'report_id')
    visible_section_lines = fields.Boolean(default=False)
    section_lines_field_ids = fields.One2many('reporting.custom.template.section.line', 'report_id')
    visible_section_footer = fields.Boolean(default=False)
    section_footer_field_ids = fields.One2many('reporting.custom.template.section.footer', 'report_id')
    visible_watermark = fields.Boolean(default=False)
    watermark = fields.Binary()
    watermark_opacity = fields.Selection([("%.2f" % x, "%.2f" % x) for x in float_range(start=0.12, stop=0.88, step=0.04)], string="Watermark Opacity")
    watermark_size = fields.Selection([('220px', 'Small'), ('400px', 'Medium'), ('600px', 'Large')], default='400px')
    amount_in_text_visible = fields.Boolean(default=False)
    amount_in_text_applicable = fields.Boolean(string="Amount In Text")
    amount_in_text_label = fields.Char(string="Label")
    section_other_option_ids = fields.One2many("reporting.custom.template.section.option", "report_id")
    font_size = fields.Selection([(str(x), str(x)) for x in range(10, 29)], string="Font Size", default="16")
    font_family = fields.Selection(FONT_LIST, string="Font Family", default=False)
    date_format = fields.Selection(DATE_FORMATS, default=DATE_FORMATS[0][0])
    show_header = fields.Boolean("Show Header ?", default=True)
    show_footer = fields.Boolean("Show Footer ?", default=True)
    paperformat_id = fields.Many2one('report.paperformat', 'Paper Format')

    def get_template(self, name):
        return self.search([('name', '=', name.strip())], limit=1)

    def get_watermark_style(self):
        self.ensure_one()
        opacity = self.watermark_opacity or "0.22"
        size = self.watermark_size or "400px"
        left = {"220px": "38%", "400px": "29%", "600px": "18%"}.get(size, "29%")

        style = "position:absolute;left:{left};width:{size};height:auto;padding-top:40px;opacity:{opacity};".format(
            opacity=opacity,
            size=size,
            left=left,
        )
        return style

    def get_field_data(self, obj, field_id, display_field=None, currency_field_name=None, thousands_separator=None):
        self.ensure_one()
        value = getattr(obj, field_id.name)
        if field_id.ttype == 'char':
            return value or ""
        elif field_id.ttype == 'many2one':
            if not value:
                return ""

            result = value.display_name
            if display_field:
                result = getattr(value, display_field)
            return result
            # return display_field and getattr(value, display_field) or value.display_name

        elif field_id.ttype == 'date':
            if not value:
                return ""
            date_format = self.date_format or DATE_FORMATS[0][0]
            return value.strftime(date_format.split('_')[1]) or ""
        elif field_id.ttype in ['float', 'integer']:
            if thousands_separator and thousands_separator == 'applicable':
                value = add_thousands_separator(value)
            return value

        elif field_id.ttype == 'many2many':
            value = ', '.join(map(lambda x: (display_field and getattr(x, display_field) or x.display_name), value))
            return value
        elif field_id.ttype == 'monetary':
            if thousands_separator and thousands_separator == 'applicable':
                value = add_thousands_separator(value)

            with_currency = str(value)

            curr_field = currency_field_name or 'currency_id'
            currency_id = getattr_new(obj, curr_field)
            if currency_id:
                if currency_id.position == 'before':
                    with_currency = currency_id.symbol + ' ' + with_currency
                else:
                    with_currency = with_currency + ' ' + currency_id.symbol
            return with_currency

        return str(value)

    def get_address_data(self, obj, o2m_field_id_name):
        self.ensure_one()

        vals = []
        for line in getattr(self, o2m_field_id_name).sorted(key=lambda r: r.sequence):
            if not line.field_id:
                continue

            value = self.get_field_data(obj=obj, field_id=line.field_id, display_field=line.field_display_field_id.name)

            prefix = ""
            if hasattr(line, 'prefix'):
                prefix = line.prefix
            separator = {'next_line': '<br/>', 'comma': ','}.get(prefix, "")

            vals.append({
                'label': line.label and line.label.strip(),
                'value': value,
                'separator': separator,
            })
        return vals

    def get_o2m_data(self, obj, o2m_field_id_name):
        self.ensure_one()

        vals = []
        for line in getattr(self, o2m_field_id_name).sorted(key=lambda r: r.sequence):
            if not line.field_id:
                continue

            thousands_separator = hasattr(line, 'thousands_separator') and line.thousands_separator or False
            value = self.get_field_data(obj=obj, field_id=line.field_id, display_field=line.field_display_field_id.name, thousands_separator=thousands_separator)

            vals.append({
                'label': line.label and line.label.strip() or line.field_id.field_description,
                'value': value,
                'null_value_display': hasattr(line, 'null_value_display') and line.null_value_display or False
            })
        return vals

    def get_o2m_data_lines_section(self, obj, line_field_name, o2m_field_id_name):
        self.ensure_one()

        data = []
        # Header
        vals = []
        for line in getattr(self, o2m_field_id_name).sorted(key=lambda r: r.sequence):
            if not line.field_id:
                continue

            vals.append({
                'type': 'header',
                'field_name': line.field_id.name,
                'label': line.label and line.label.strip() or line.field_id.field_description,
                'value': False,
                'null_hide_column': line.null_hide_column,
                'invisible': False,
                'width_style': 'width:%s' % (line.width or 'auto'),
            })
        data.append(vals)

        # Content
        for each in getattr(obj, line_field_name):
            vals = []
            for line in getattr(self, o2m_field_id_name).sorted(key=lambda r: r.sequence):
                if not line.field_id:
                    continue

                value = self.get_field_data(obj=each, field_id=line.field_id, display_field=line.field_display_field_id.name, currency_field_name=line.currency_field_name, thousands_separator=line.thousands_separator)
                vals.append({
                    'type': 'content',
                    'field_name': line.field_id.name,
                    'label': line.label and line.label.strip() or line.field_id.field_description,
                    'value': value,
                    'null_hide_column': line.null_hide_column,
                    'invisible': False,
                    'alignment_style': 'text-align:%s' % (line.alignment or 'left'),
                    'line_id': each,
                })
            data.append(vals)

        # null_hide_column
        field_data = {}
        for row in data:
            for col in row:
                if col['null_hide_column']:
                    field_name = col['field_name']
                    value = col['value']
                    if field_name in field_data:
                        field_data[field_name].append(value)
                    else:
                        field_data[field_name] = [value]

        for row in data:
            for col in row:
                if col['null_hide_column']:
                    val_list = field_data.get(col['field_name']) or []
                    if not any(val_list):
                        col['invisible'] = True
        return data

    def get_colors(self):
        self.ensure_one()
        colors = ColorObject()

        colors.color1 = self.template_id.color1
        colors.color2 = self.template_id.color2
        colors.color3 = self.template_id.color3

        return colors

    def get_font(self):
        self.ensure_one()
        font = Font()

        if self.font_size:
            font.size = "%spx" % self.font_size

        if self.font_family:
            font.family = self.font_family
        return font

    @staticmethod
    def get_amount_in_text(obj, field_name, currency_field='currency_id'):
        currency_id = getattr_new(obj, currency_field)
        if not currency_id:
            return ""

        amount = getattr_new(obj, field_name)
        text = currency_id.amount_to_text(amount)
        return text

    def get_other_option_data(self, technical_name, remove_break=False):
        self.ensure_one()
        for each in self.section_other_option_ids:
            if each.name_technical == technical_name:
                result = each.get_value()

                if remove_break and type(result) == str:
                    result = result.replace("<br/>", " ")
                return result

        return False


class ReportingTemplateTemplateTemplate(models.Model):
    _name = 'reporting.custom.template.template'

    name = fields.Char(required=True)
    name_technical = fields.Char(required=True)
    report_name = fields.Char()
    color1 = fields.Char()
    color2 = fields.Char()
    color3 = fields.Char()
    image = fields.Binary()


class ReportingTemplateHeaderSection(models.Model):
    _name = 'reporting.custom.template.header.field'

    report_id = fields.Many2one('reporting.custom.template')
    sequence = fields.Integer('Sequence', default=10)
    prefix = fields.Selection(SEPARATORS, string='Start With')
    field_id = fields.Many2one('ir.model.fields', domain=[('model_id.model', '=', 'res.company')])
    field_type = fields.Selection('Field Type', related='field_id.ttype', readonly=True)
    field_relation = fields.Char(related='field_id.relation', readonly=True)
    field_display_field_id = fields.Many2one('ir.model.fields', string="Display Field", domain="[('model_id.model', '=', field_relation)]")
    # display_field_name = fields.Char(string='Display Field') # Archived
    label = fields.Char(string='Label')


class ReportingTemplateFooterSection(models.Model):
    _name = 'reporting.custom.template.footer.field'

    report_id = fields.Many2one('reporting.custom.template')
    sequence = fields.Integer('Sequence', default=10)
    field_id = fields.Many2one('ir.model.fields', domain=[('model_id.model', '=', 'res.company')])
    field_type = fields.Selection('Field Type', related='field_id.ttype', readonly=True)
    field_relation = fields.Char(related='field_id.relation', readonly=True)
    field_display_field_id = fields.Many2one('ir.model.fields', string="Display Field", domain="[('model_id.model', '=', field_relation)]")
    # display_field_name = fields.Char(string='Display Field')
    label = fields.Char(string='Label')


class ReportingTemplatePartnerSection(models.Model):
    _name = 'reporting.custom.template.partner.field'

    report_id = fields.Many2one('reporting.custom.template')
    sequence = fields.Integer('Sequence', default=10)
    prefix = fields.Selection(SEPARATORS, string='Start With')
    field_id = fields.Many2one('ir.model.fields', domain=[('model_id.model', '=', 'res.partner')])
    field_type = fields.Selection('Field Type', related='field_id.ttype', readonly=True)
    field_relation = fields.Char(related='field_id.relation', readonly=True)
    field_display_field_id = fields.Many2one('ir.model.fields', string="Display Field", domain="[('model_id.model', '=', field_relation)]")
    # display_field_name = fields.Char(string='Display Field')
    label = fields.Char(string='Label')


class ReportingTemplateSection2(models.Model):
    _name = 'reporting.custom.template.section.2'

    report_id = fields.Many2one('reporting.custom.template')
    sequence = fields.Integer('Sequence', default=10)
    model_id = fields.Many2one('ir.model', related='report_id.model_id', readonly=True)
    field_id = fields.Many2one('ir.model.fields', domain="[('model_id', '=', model_id)]")
    field_type = fields.Selection('Field Type', related='field_id.ttype', readonly=True)
    field_relation = fields.Char(related='field_id.relation', readonly=True)
    field_display_field_id = fields.Many2one('ir.model.fields', string="Display Field", domain="[('model_id.model', '=', field_relation)]")
    label = fields.Char(string='Label')
    null_value_display = fields.Boolean(string='Display Null')


class ResCompany(models.Model):
    _inherit = 'res.company'

    @staticmethod
    def get_template_report_font_assets():
        body = ""
        for each in get_all_font_list(with_extension=True):
            body += """@font-face {font-family: '%s'; src: URL('/report_utils/static/fonts/%s') format('truetype');}
            """ % (rchop(each[0], ".ttf"), each[0])
        return "<style>%s</style>" % body
