# -*- coding: utf-8 -*-
from io import BytesIO
import base64
import datetime
from ast import literal_eval
from odoo import api, fields, models
import xlwt


class ProductStockExpiration(models.TransientModel):
    _name = "product.stock.expiration"

    report_days = fields.Integer(
        string="Generate Report For(Next Days)",
        required=True,
        help="Number of days product will be expire in stock")
    include_expire_stock = fields.Boolean(
        string="Include Expire Stock",
        help="Past and Future product stock expire report form select Include Expire Stock.")
    report_type = fields.Selection(
        [('all', 'All'), ('location', 'Location')],
        string='Report Type', default='all',
        help="Filter based on location wise and all stock product expiration report")
    location_ids = fields.Many2many(
        "stock.location", string="Filter by Locations",
        help="Check Product Stock for Expiration from selected Locations only. " \
        "if its blank it checks in all Locations")

    @api.multi
    def print_product_stock_expiration_report(self, rer):
        data = {}
        data['form'] = (self.read(['report_days', 'include_expire_stock',
                                   'report_type', 'location_ids'])[0])
        return self.env.ref('product_expiration_alert.action_report_product_stock_expiration').\
            report_action(self, data=data, config=False)

    @api.model
    def default_get(self, fields):
        rec = super(ProductStockExpiration, self).default_get(fields)
        get_param = self.env['ir.config_parameter'].sudo().get_param
        rec['report_days'] = literal_eval(get_param('product_expiration_alert.report_days'))
        rec['include_expire_stock'] = get_param('product_expiration_alert.include_expire_stock')
        rec['report_type'] = get_param('product_expiration_alert.report_type')
        rec['location_ids'] = literal_eval(get_param('product_expiration_alert.location_ids'))
        return rec

    def get_product_location(self, quant_ids):
        """ get product location from LOT/Serial number"""

        location_list = []
        for quant_id in quant_ids:
            if self.report_type == 'location':
                if quant_id.location_id in self.location_ids:
                    location_list.append(quant_id.location_id.display_name)
            else:
                if quant_id.location_id.usage == 'internal':
                    location_list.append(quant_id.location_id.display_name)

        return ', '.join(location_list)

    @api.multi
    def product_stock_expiration_excel_report(self):
        filename = 'Product Stock Expiration Report''.xls'
        workbook = xlwt.Workbook(encoding="UTF-8")

        worksheet = workbook.add_sheet('Product Stock Expiry Report')
        font = xlwt.Font()
        font.bold = True
        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250;' \
            'align: vertical center, horizontal center, wrap on;' \
            'borders: top double, bottom double, left double, right double;')
        style = xlwt.easyxf('font:height 400, bold True, name Arial; ' \
                            'align: horiz center, vert center;' \
                            'borders: top medium, right medium, bottom medium, left medium')
        for_left_center = xlwt.easyxf("font: color black; align: horiz left")
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_RIGHT
        style = xlwt.easyxf('align: wrap yes')
        style.num_format_str = '0.00'

        worksheet.row(0).height = 320
        worksheet.col(0).width = 5000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 5000
        worksheet.col(5).width = 6000
        worksheet.col(6).width = 5000

        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle()
        border_style.borders = borders

        product_stock_expiration_title = 'Product Stock Expiry Report'
        worksheet.write_merge(0, 1, 0, 6, product_stock_expiration_title, GREEN_TABLE_HEADER)

        row = 2
        worksheet.write(row, 0, 'PRODUCT NAME' or '', for_left_center)
        worksheet.write(row, 1, 'PRODUCT NUMBER' or '', for_left_center)
        worksheet.write(row, 2, 'PRODUCT CATEGORY' or '', for_left_center)
        worksheet.write(row, 3, 'LOCATION' or '', for_left_center)
        worksheet.write(row, 4, 'QUANTITY' or '', for_left_center)
        worksheet.write(row, 5, 'LOTS/SERIAL NUMBER' or '', for_left_center)
        worksheet.write(row, 6, 'EXPIRY DATE' or '', for_left_center)

        return_list = {}
        StockProductionObj = self.env['stock.production.lot']
        return_list['report_days'] = self.report_days
        current_date = datetime.date.today() + datetime.timedelta(days=self.report_days)
        domain = [('use_date', '<', str(current_date))]
        if not self.include_expire_stock:
            domain += [('use_date', '>', str(fields.Datetime.now()))]
        if self.report_type == 'location':
            domain += [('quant_ids.location_id', 'in', self.location_ids.ids)]
        lot_ids = StockProductionObj.search(domain)

        seq = 0
        for lot_id in lot_ids.filtered(lambda lot_id: lot_id.product_qty > 0):
            for quant in lot_id.quant_ids.filtered(lambda k: k.location_id.usage == 'internal'):
                if self.report_type == 'all' or (self.report_type == 'location' and \
                                                 quant.location_id.id in self.location_ids.ids):
                    seq = seq + 1
                    row = row + 1
                    worksheet.write(row, 0, lot_id.product_id.display_name or '', for_left_center)
                    worksheet.write(row, 1, lot_id.product_id.default_code or '', for_left_center)
                    worksheet.write(row, 2, lot_id.product_id.categ_id.display_name or '',
                                    for_left_center)
                    worksheet.write(row, 3, quant.location_id.display_name or '', for_left_center)
                    worksheet.write(row, 4, quant.quantity or 0.0, for_left_center)
                    worksheet.write(row, 5, lot_id.name or '', for_left_center)
                    use_date = lot_id.use_date.strftime('%d/%m/%Y') \
                        if lot_id.use_date else ''
                    worksheet.write(row, 6, use_date, for_left_center)

        fp = BytesIO()
        workbook.save(fp)
        stock_expiration_excel_id = self.env['stock.expiration.report.excel.extended'].create(
            {'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
        fp.close()

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_xls_report/%s' % (stock_expiration_excel_id.id),
            'target': 'new',
        }

class ProductStockReportExcelExtended(models.Model):
    _name = "stock.expiration.report.excel.extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)
