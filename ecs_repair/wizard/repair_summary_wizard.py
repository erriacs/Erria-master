""" Repair Summary Wizard """
import base64
import io
import xlsxwriter
import pytz
from odoo import models, fields, _
from odoo.exceptions import UserError


class RepairSummaryWizard(models.TransientModel):
    """ Defining repair summary wizard """

    _name = "repair.summary.wizard"
    _description = "Repair Summary Wizard"

    filename = fields.Char(size=256, readonly=True)
    data_binary = fields.Binary('Content Data', readonly=True)

    def _parse_data(self, repair):
        """ parsing repair data """

        rep_data = []
        for rep in repair:
            for line in rep.estimation_line_ids.filtered(lambda r: r.approved):
                vals = {'name': line.repair_order_id.name,
                        'container': line.repair_order_id.container_label,
                        'code': line.repair_code,
                        'completion_date': line.repair_order_id.completion_date,
                        'labour_price': line.quantity * line.labour_price,
                        'material_price': line.quantity * line.material_price,
                        'subtotal': line.price_subtotal,
                        'taxes': line.price_tax,
                        'total': line.price_total}
                rep_data.append(vals)
        return rep_data

    def generate_report(self, rep_data):
        """ Generate xls """

        bz_data = io.BytesIO()
        workbook = xlsxwriter.Workbook(bz_data)
        filename = 'Summary %s.xls' % (rep_data.get('customer', ''))
        sheet = workbook.add_worksheet('Repair Summary')
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)

        ###########################################
        title_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': 1})
        title_center.set_font_name('Arial')
        title_center.set_font_size('18')
        title_center.set_text_wrap()
        ###########################################
        table_header = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': 1})
        table_header.set_font_name('Arial')
        table_header.set_font_size('11')
        table_header.set_bottom()
        table_header.set_text_wrap()
        ###########################################
        normal_center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        normal_center.set_font_name('Arial')
        normal_center.set_font_size('11')
        normal_center.set_text_wrap()
        ###########################################
        normal_left = workbook.add_format({'align': 'left'})
        normal_left.set_font_name('Arial')
        normal_left.set_font_size('11')
        normal_left.set_text_wrap()
        ###########################################
        normal_right = workbook.add_format({'align': 'right'})
        normal_right.set_font_name('Arial')
        normal_right.set_num_format('#,##0')
        normal_right.set_font_size('11')
        normal_right.set_text_wrap()
        ###########################################
        total_left = workbook.add_format({'align': 'left', 'bold': 1})
        total_left.set_font_name('Arial')
        total_left.set_font_size('11')
        total_left.set_top()
        total_left.set_text_wrap()
        ###########################################
        total_right = workbook.add_format({'align': 'right', 'bold': 1})
        total_right.set_font_name('Arial')
        total_right.set_num_format('#,##0')
        total_right.set_font_size('11')
        total_right.set_top()
        total_right.set_text_wrap()

        sheet.set_row(0, 40)
        sheet.merge_range('C1:E1', 'Repair Order Summary', title_center)
        sheet.write('B3', 'Customer', normal_left)
        sheet.merge_range('C3:D3', rep_data.get('customer', ''), normal_center)
        sheet.write('E3', 'Currency', normal_left)
        sheet.write('F3', rep_data.get('currency', ''), normal_center)
        sheet.write('B4', 'Printed Date', normal_left)
        pdate = rep_data.get('date').strftime('%H:%M %d/%m/%Y') if rep_data.get('date') \
            else ''
        sheet.merge_range('C4:D4', pdate, normal_center)
        sheet.set_row(5, 35)
        sheet.write('A6', 'No', table_header)
        sheet.write('B6', 'Repair Reference', table_header)
        sheet.write('C6', 'Container ID', table_header)
        sheet.write('D6', 'Customer Repair Code', table_header)
        sheet.write('E6', 'Completed Date', table_header)
        sheet.write('F6', 'Labour Price', table_header)
        sheet.write('G6', 'Material Price', table_header)
        sheet.write('H6', 'Total Before Taxes', table_header)
        sheet.write('I6', 'Taxes', table_header)
        sheet.write('J6', 'Total', table_header)
        ln_num = 1
        ln_row = 8
        tlabour = 0
        tmaterial = 0
        ttaxes = 0
        tsubtotal = 0
        ttotal = 0
        for line in rep_data.get('data'):
            sheet.write('A'+str(ln_row), ln_num, normal_center)
            sheet.write('B'+str(ln_row), line.get('name'), normal_left)
            sheet.write('C'+str(ln_row), line.get('container'), normal_left)
            sheet.write('D'+str(ln_row), line.get('code'), normal_center)
            cmp_date = line.get('completion_date').strftime('%d/%m/%Y') \
                if line.get('completion_date') else ''
            sheet.write('E'+str(ln_row), cmp_date, normal_right)
            sheet.write('F'+str(ln_row), line.get('labour_price', None), normal_right)
            sheet.write('G'+str(ln_row), line.get('material_price', None), normal_right)
            sheet.write('H'+str(ln_row), line.get('subtotal', None), normal_right)
            sheet.write('I'+str(ln_row), line.get('taxes', None), normal_right)
            sheet.write('J'+str(ln_row), line.get('total', None), normal_right)
            ln_num += 1
            ln_row += 1
            tlabour += line.get('labour_price', 0)
            tmaterial += line.get('material_price', 0)
            ttaxes += line.get('taxes', 0)
            tsubtotal += line.get('subtotal', 0)
            ttotal += line.get('total', 0)
        if rep_data.get('data'):
            sheet.write('A'+str(ln_row+1), '', total_right)
            sheet.write('B'+str(ln_row+1), '', total_right)
            sheet.write('C'+str(ln_row+1), '', total_right)
            sheet.write('D'+str(ln_row+1), '', total_right)
            sheet.write('E'+str(ln_row+1), 'TOTAL', total_left)
            sheet.write('F'+str(ln_row+1), tlabour, total_right)
            sheet.write('G'+str(ln_row+1), tmaterial, total_right)
            sheet.write('H'+str(ln_row+1), tsubtotal, total_right)
            sheet.write('I'+str(ln_row+1), ttaxes, total_right)
            sheet.write('J'+str(ln_row+1), ttotal, total_right)
        workbook.close()
        out = base64.encodestring(bz_data.getvalue())
        rep_data.get('wiz').write({'data_binary': out, 'filename': filename})
        bz_data.close()
        action = {
            'name': 'Repair Order Summary',
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=repair.summary.wizard&id='+str(rep_data.get('wiz').id)+\
                '&filename_field=filename&field=data_binary&download=true&filename='+filename,
            'target': 'new'}
        return action

    def generate_summary(self):
        """ Generate repair summary """

        repair = self.env['repair.order'].browse(self._context.get('active_ids', []))
        taxes = []
        for rep in repair:
            taxes += rep.estimation_line_ids.mapped('tax_ids')
        if len(repair.mapped('partner_id')) > 1:
            raise UserError(_("Can only generate summary for orders of a customer!"))
        elif len(repair.mapped('currency_id')) > 1:
            raise UserError(_("Can only generate summary for orders with similar currency!"))
        elif any(state != 'to_review' for state in repair.mapped('state')):
            raise UserError(_("Can only generate summary for Ready to Review orders!"))
        rep_data = self._parse_data(repair)
        customer = repair[0].partner_id.name if repair and repair[0].partner_id \
            else False
        currency = repair[0].currency_id.name if repair and repair[0].currency_id \
            else False
        tzname = self.env.user.tz or self._context.get('tz') or 'UTC'
        tzname = pytz.timezone(tzname)
        dtime = pytz.utc.localize(fields.Datetime.now(), is_dst=False)
        dtime = dtime.astimezone(tzname)
        data = {'data': rep_data,
                'date': dtime,
                'customer': customer,
                'currency': currency,
                'wiz': self}
        return self.generate_report(data)
