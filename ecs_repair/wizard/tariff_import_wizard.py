""" Repair Summary Wizard """
import base64
import os
import logging
from odoo import models, fields, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
try:
    import xlrd
except (ImportError, IOError) as err:
    _logger.debug(err)


class TariffImportWizard(models.TransientModel):
    """ Defining Import Tariff Wizard """

    _name = "import.tariff.wizard"
    _description = "Import Tariff Wizard"

    file_name = fields.Char(required=True)
    file = fields.Binary('Tariff Data')
    tariff_id = fields.Many2one('repair.tariff')

    def get_product(self, name):
        """ Get Product """

        product = self.env['product.product'].search(
            ['|', ('name', '=', name), ('default_code', '=', name)], limit=1)
        if not product:
            raise UserError(_("Can't find product %s!" % name))
        return product

    def get_component(self, comp, comp_list):
        """ Get Component """

        if comp:
            component = self.env['repair.component'].search_read(
                domain=[('code', '=', comp)], fields=['id'], limit=1)
            if component:
                comp_list.append({'code': comp, 'id': component[0].get('id')})
                comp = component[0].get('id')
            else:
                raise UserError(_("Can't find component with code %s!" % comp))
        return comp, comp_list

    def get_location(self, loc, loc_list):
        """ Get Location """

        if loc:
            location = self.env['repair.location'].search_read(
                domain=[('code', '=', loc)], fields=['id'], limit=1)
            if location:
                loc_list.append({'code': loc, 'id': location[0].get('id')})
                loc = location[0].get('id')
            else:
                raise UserError(_("Can't find repair location with code %s!" % loc))
        return loc, loc_list

    def get_damage(self, dam, dam_list):
        """ Get Component """

        if dam:
            damage = self.env['damage.type'].search_read(
                domain=[('code', '=', dam)], fields=['id'], limit=1)
            if damage:
                dam_list.append({'code': dam, 'id': damage[0].get('id')})
                dam = damage[0].get('id')
            else:
                raise UserError(_("Can't find damage type with code %s!" % dam))
        return dam, dam_list

    def get_repair(self, rep, rep_list):
        """ Get Component """

        if rep:
            repair = self.env['repair.types'].search_read(
                domain=[('code', '=', rep)], fields=['id'], limit=1)
            if repair:
                rep_list.append({'code': rep, 'id': repair[0].get('id')})
                rep = repair[0].get('id')
            else:
                raise UserError(_("Can't find repair type with code %s!" % rep))
        return rep, rep_list

    def tariff_import(self):
        """ Custom Tariff Import """

        if not self.file:
            raise UserError(_('There is no file selected!' \
                              'Please select file to import first'))
        files = os.path.splitext(self.file_name)
        if files[1] not in ('.xls', '.xlsx'):
            raise UserError(_('Invalid file format! Can only import from xls or xlsx format'))

        workbook = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
        sheet = workbook.sheet_by_index(0)
        if sheet.nrows < 2:
            raise UserError(_('No data in the file'))
        #mapping product
        product = []
        for row in range(0, 1):
            for col in range(10, sheet.ncols):
                prd = sheet.cell(row, col).value
                check = [x for x in product if product and prd and x.get('name') == prd.upper()]
                if not check:
                    new_product = self.get_product(prd.upper())
                    product.append({'name': prd.upper(), 'col': col, 'product': new_product})
                else:
                    raise UserError(_('Duplicate product column for %s!' % prd))
        data = []
        comp_list, loc_list, dam_list, rep_list = [], [], [], []
        for row in range(1, sheet.nrows):
            comp = str(sheet.cell(row, 0).value) \
                if sheet.cell(row, 0).value else ''
            check_comp = [x for x in comp_list if comp_list and comp and x.get('code') == comp]
            if not check_comp:
                comp, comp_list = self.get_component(comp.upper(), comp_list)
            else:
                comp = check_comp[0].get('id')
            loc = str(sheet.cell(row, 1).value) \
                if sheet.cell(row, 1).value else ''
            check_loc = [x for x in loc_list if loc_list and loc and x.get('code') == loc]
            if not check_loc:
                loc, loc_list = self.get_location(loc.upper(), loc_list)
            else:
                loc = check_loc[0].get('id')
            dam = str(sheet.cell(row, 2).value) \
                if sheet.cell(row, 2).value else ''
            check_dam = [x for x in dam_list if dam_list and dam and x.get('code') == dam]
            if not check_dam:
                dam, dam_list = self.get_damage(dam.upper(), dam_list)
            else:
                dam = check_dam[0].get('id')
            rep = str(sheet.cell(row, 3).value) \
                if sheet.cell(row, 3).value else ''
            check_rep = [x for x in rep_list if rep_list and rep and x.get('code') == rep]
            if not check_rep:
                rep, rep_list = self.get_repair(rep.upper(), rep_list)
            else:
                rep = check_rep[0].get('id')
            leng = float(sheet.cell(row, 4).value) \
                if sheet.cell(row, 4).value else 0.0
            wid = float(sheet.cell(row, 5).value) \
                if sheet.cell(row, 5).value else 0.0
            code = str(sheet.cell(row, 7).value) \
                if sheet.cell(row, 7).value else ""
            if not all([comp, loc, dam, rep, code]):
                raise UserError(
                    _("Component, Location, Damage, Repair Type," \
                      " and Repair Code in row %s must be filled!" % (row+1)))
            qty = float(sheet.cell(row, 6).value) \
                if sheet.cell(row, 6).value else 0.0
            sts = str(sheet.cell(row, 8).value) \
                if sheet.cell(row, 8).value else 0.0
            mat = str(sheet.cell(row, 9).value) \
                if sheet.cell(row, 9).value else 0.0
            # check duplicate line
            check = [x for x in data if data and x[2].get('component_id') == comp \
                     and x[2].get('location_id') == loc and x[2].get('damage_type') == dam \
                     and x[2].get('repair_type_id') == rep and x[2].get('length') == leng \
                     and x[2].get('width') == wid and x[2].get('quantity') == qty \
                     and x[2].get('repair_code') == code and x[2].get('sts') == sts]
            if check:
                raise UserError(_('Duplicate data in row %s!' % (row+1)))
            material = []
            for col in range(10, sheet.ncols):
                prd_qty = float(sheet.cell(row, col).value) \
                    if sheet.cell(row, col).value else False
                if prd_qty:
                    prd_line = [x for x in product if product and x.get('col') == col]
                    vals = {'product_id': prd_line[0].get('product').id,
                            'name': prd_line[0].get('product').name,
                            'quantity': prd_qty,
                            'uom_id': prd_line[0].get('product').uom_id.id}
                    material.append((0, 0, vals))
            line_vals = {'component_id': comp, 'location_id': loc,
                         'damage_type': dam, 'repair_type_id': rep,
                         'length': leng, 'width': wid, 'quantity': qty, 'repair_code': code,
                         'sts': sts, 'material_price': mat, 'material_line_ids': material}
            data.append((0, 0, line_vals))
        if data:
            self.tariff_id.write({'tariff_line_ids': data})
