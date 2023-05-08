""" Repair Order """
import base64
from io import BytesIO
import logging
import zipfile
from odoo import fields, models, api, _
from odoo.tools import image_resize_image, ustr
from odoo.exceptions import ValidationError, UserError
_logger = logging.getLogger(__name__)
from stdnum import iso6346


class RepairOrder(models.Model):
    """" Inherit Repair Order"""

    _inherit = 'repair.order'

    @api.depends('estimation_line_ids.price_total',
                 'estimation_line_ids.approved',
                 'estimation_line_ids.sts',
                 'damage_line_ids')
    def _compute_amount(self):
        """ Compute sum of estimation """

        for repair in self:
            sts = 0.0
            untaxed = taxes = 0.0
            for line in repair.estimation_line_ids.filtered(lambda r: r.approved):
                untaxed += line.price_subtotal
                taxes += line.price_tax
                sts += line.sts
            repair.update(
                {'amount_tax_estimation': taxes,
                 'amount_untaxed_estimation': untaxed,
                 'amount_total_estimation': taxes + untaxed,
                 'sts_estimation': sts})

    @api.depends('parts_line_ids.purchase_price_subtotal')
    def _compute_parts_cost(self):
        """ Compute total parts cost """

        for repair in self:
            cost = sum(repair.parts_line_ids.mapped('purchase_price_subtotal'))
            repair.update({'amount_parts_cost': cost})

    @api.depends('work_order_line_ids.repair_time')
    def _compute_repair_time(self):
        """ Compute actual repair time """

        for order in self:
            time_spent = sum(order.work_order_line_ids.filtered(
                lambda r: r.state == 'done' and r.qc_status == 'passed').mapped('repair_time'))
            order.update({'repair_time': time_spent})

    @api.depends('work_order_line_ids')
    def _compute_work_order_line(self):
        for order in self:
            order.work_order_line_count = len(order.work_order_line_ids)


    amount_parts_cost = fields.Monetary(compute='_compute_parts_cost', store=True)
    amount_tax_estimation = fields.Monetary(compute='_compute_amount', store=True)
    amount_total_estimation = fields.Monetary(compute='_compute_amount', store=True)
    amount_untaxed_estimation = fields.Monetary(compute='_compute_amount', store=True)
    approval_date = fields.Datetime()
    container_label = fields.Char(string="Container ID")
    completion_date = fields.Datetime('Actual Repair Completion Date')
    company_currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.ref('base.main_company').currency_id)
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self:
                                  self.env.ref('base.main_company').currency_id)
    damage_line_ids = fields.One2many('repair.order.damage',
                                      'repair_order_id', copy=False)
    edi_partner = fields.Boolean(related='partner_id.edi_partner')
    estimation_date = fields.Datetime()
    estimation_line_ids = fields.One2many('repair.order.estimation',
                                          'repair_order_id', copy=False)
    invoice_method = fields.Selection(
        [('none', 'No Invoice'),
         ('b4repair', 'Before Repair'),
         ('after_repair', 'After Repair')],
        default='after_repair')
    line_sequence = fields.Integer(default=0, copy=False)
    mode_id = fields.Many2one('repair.mode')
    parts_line_ids = fields.One2many('repair.order.parts',
                                     'repair_order_id', copy=False)
    planned_date = fields.Datetime('Planned Date of Repair')
    posting_date = fields.Datetime()
    qc_staff_id = fields.Many2one('hr.employee', string="QC Staff")
    reference = fields.Char()
    repair_cause = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')])
    repair_date = fields.Datetime()
    repair_operation_id = fields.Many2one('stock.picking.type')
    repair_time = fields.Float(string="Time spent (hours)", compute='_compute_repair_time')
    return_repair_operation_id = fields.Many2one('stock.picking.type')
    shop_code = fields.Char()
    state = fields.Selection(selection_add=[
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('reject', 'Reject'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('to_review', 'Ready to Review'),
        ('to_complete', 'Review to Complete'),
        ('draft_invoice', 'Draft Invoice'),
        ('invoiced', 'Invoiced'),
        ('rework', 'Rework')])
    sts_estimation = fields.Float('Total STS', compute='_compute_amount')
    surveyor_id = fields.Many2one('hr.employee')
    tariff_id = fields.Many2one('repair.tariff', ondelete='restrict')
    third_party_location = fields.Char(size=3)
    warehouse_id = fields.Many2one('stock.warehouse', string='Depot')
    work_order_line_ids = fields.One2many('repair.work.order',
                                          'repair_order_id', copy=False)
    wo_type = fields.Selection([('W', 'W'), ('O', 'O')],
                               default='W')
    public_ids = fields.One2many('public.document', 'repair_order_id', copy=False)
    partner_id = fields.Many2one(
        'res.partner', 'Customer', domain=[('customer', '=', True)],
        index=True, states={'confirmed': [('readonly', True)]}, change_default=True,
        help='Choose partner for whom the order will be invoiced and delivered. You can find a partner by its Name, TIN, Email or Internal Reference.')
    work_order_line_count = fields.Integer(compute="_compute_work_order_line", string='Bill Count', copy=False, default=0, store=True)
    detail_reason = fields.Text('Reason Detail', translate=True, track_visibility='onchange')

    LABEL_MAP = {
        'A': 10,
        'B': 12,
        'C': 13,
        'D': 14,
        'E': 15,
        'F': 16,
        'G': 17,
        'H': 18,
        'I': 19,
        'J': 20,
        'K': 21,
        'L': 23,
        'M': 24,
        'N': 25,
        'O': 26,
        'P': 27,
        'Q': 28,
        'R': 29,
        'S': 30,
        'T': 31,
        'U': 32,
        'V': 34,
        'W': 35,
        'X': 36,
        'Y': 37,
        'Z': 38,
    }

    def validation_container_label(self, container_label):
        """ Checking container label before create/write """
        result = False
        if container_label:
            try:
                result = iso6346.validate(container_label)
            except Exception as e:
                pass

        if not result:
            raise ValidationError('Container ID is wrong.')

    @api.multi
    def action_view_repair_item(self):
        work_order_line_ids = self.mapped('work_order_line_ids')
        action = self.env.ref('ecs_repair.action_repair_work_order').read()[0]
        if len(work_order_line_ids) > 1:
            action['domain'] = [('id', 'in', work_order_line_ids.ids)]
        elif len(work_order_line_ids) == 1:
            form_view = [(self.env.ref('ecs_repair.repair_work_order_view_form').id, 'form')]
            action['views'] = form_view
            action['res_id'] = work_order_line_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_sn_sequence(self):
        for repair in self:
            sn_num = 1
            for line in repair.damage_line_ids:
                line.seq_num = sn_num
                sn_num += 1

    def print_repair_eor(self):
        return self.env.ref('ecs_repair.eor_report').with_context(discard_logo_check=True).report_action(self)

    def action_sn_estimation(self):
        for repair in self:
            sn_num = 1
            for line in repair.estimation_line_ids:
                line.seq_num = sn_num
                sn_num += 1

    def action_generate_image_sequence(self):
        for repair in self:
            img_num = 1
            for line in repair.damage_line_ids:
                for doc in line.public_ids:
                    if doc.document_name:
                        fname = "%s(%s).%s" % (
                            self.container_label, img_num, doc.document_name.rsplit('.')[1])
                        
                        doc.document_name = fname
                        img_num += 1

    @api.depends('picking_ids')
    def _compute_picking(self):
        """ count total picking """
        for order in self:
            if order.picking_ids:
                order.update({'picking_counts': len(self.picking_ids)})
            else:
                order.update({'picking_counts': 0})

    @api.multi
    @api.onchange('warehouse_id')
    def _onchange_warehouse(self):
        """ on change warehouse """

        for order in self:
            ret_picking_type = self.env['stock.picking.type'].search_read(
                domain=[('warehouse_id', '=', order.warehouse_id.id),
                        ('default_location_src_id.usage', '=', 'production'),
                        ('return_repair', '=', True),
                        ('default_location_dest_id.usage', '=', 'internal')],
                fields=['id'], limit=1)
            ret_picking_type = ret_picking_type[0].get('id') if ret_picking_type \
                else False
            picking_type = self.env['stock.picking.type'].search_read(
                domain=[('warehouse_id', '=', order.warehouse_id.id),
                        ('default_location_src_id.usage', '=', 'internal'),
                        ('repair', '=', True),
                        ('default_location_dest_id.usage', '=', 'production')],
                fields=['id'], limit=1)
            picking_type = picking_type[0].get('id') if picking_type else False
            vals = {'return_repair_operation_id': ret_picking_type,
                    'repair_operation_id': picking_type}
            order.update(vals)

    @api.multi
    @api.onchange('partner_id')
    def _onchange_partner(self):
        """ On change partner """

        for order in self:
            tariff = self.env['repair.tariff'].search_read(
                domain=[('partner_id', '=', order.partner_id.id)],
                fields=['id', 'currency_id'], limit=1)
            if tariff:
                currency = tariff[0].get('currency_id')[0] if tariff[0].get('currency_id') \
                    else self.env.user.company_id.currency_id.id
                order.update({'tariff_id': tariff[0].get('id'),
                              'currency_id': currency})
            else:
                order.update(
                    {'tariff_id': False,
                     'currency_id': self.env.user.company_id.currency_id.id})

    @api.onchange('partner_id', 'warehouse_id')
    def _onchange_partner_warehouse(self):
        """ On Change Partner Warehouse """

        if self.partner_id.edi_partner and self.warehouse_id:
            edi_line = self.partner_id.edi_line_ids.filtered(
                lambda r: r.warehouse_id == self.warehouse_id)
            shop, ref = False, False
            if edi_line:
                shop = edi_line[0].shop_code
                ref = edi_line[0].sequence_id.next_by_id()
            self.update({'shop_code': shop,
                         'reference': ref})

    @api.multi
    @api.onchange('tariff_id')
    def _onchange_tariff(self):
        """ On change tariff """

        for order in self:
            currency = order.currency_id.id if order.tariff_id.currency_id \
                else self.env.user.company_id.currency_id.id
            order.update({'currency_id': currency})

    def _get_image_attachments(self):
        public_ids = self.damage_line_ids.mapped('public_ids')
        if not public_ids:
            return None

        img_data = [(public.document_name, public.document) for public in public_ids]

        attachments = img_data.copy()
        if img_data:
            if len(img_data) >= 20:
                try:
                    fname = "%s.zip" % self.container_label
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        for file_name, data in img_data:
                            decode_data = base64.b64decode(data)
                            zip_file.writestr(file_name, decode_data)
                        zip_file.close()
                    zipres = base64.encodebytes(zip_buffer.getvalue())

                    attachments = [(fname, zipres)]
                except Exception:
                    _logger.info('Fail to compress evidence')

        return attachments

    def _send_image_files(self):
        """ Send Compressed evidence files """
        # TODO: this code may be removed in the future
        # img_data = []
        # fname = "%s.zip" % self.container_label
        # for line in self.damage_line_ids:
        #     for public in line.public_ids:
        #         lndata = base64.b64decode(public.document)
        #         img_data.append((public.document_name, lndata))
        #
        # if img_data:
        #     try:
        #         zip_buffer = BytesIO()
        #         with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        #             for file_name, data in img_data:
        #                 zip_file.writestr(file_name, data)
        #             zip_file.close()
        #         zipres = base64.encodestring(zip_buffer.getvalue())
        #         mail_template = self.env.ref('ecs_repair.email_template_edi',
        #                                      raise_if_not_found=False)
        #         if mail_template:
        #             try:
        #                 mail_template.sudo().send_mail(
        #                     self.id, force_send=True,
        #                     email_values={'email_to': self.partner_id.edi_email_images,
        #                                   'subject': self.container_label,
        #                                   'attachments':[(fname, zipres)]})
        #             except:
        #                 _logger.info('Fail to send image zip mail')
        #     except Exception:
        #         _logger.info('Fail to compress evidence')

        attachments = self._get_image_attachments()
        mail_template = self.env.ref('ecs_repair.email_template_edi', raise_if_not_found=False)
        if mail_template and attachments:
            try:
                mail_template.sudo().send_mail(
                    self.id, force_send=True,
                    email_values={'email_to': self.partner_id.edi_email_images,
                                  'subject': self.container_label,
                                  'attachments': attachments})
            except:
                _logger.info('Fail to send image mail')
        else:
            _logger.info('Image or email template not found.')

    def _send_edi_file(self):
        """ Send EDI File """

        cropped = False
        def _process_line(line):
            nonlocal cropped
            # Formatting per new requirement
            line_length = 80
            eol = "\r\n" # Template export uses Windows line endings
            line = line.splitlines()[0]
            if len(line) < line_length:
                line = line.ljust(line_length)
            if len(line) > line_length:
                line = line[:line_length]
                cropped = line_length
            line = line + eol
            return line

        ftxt = BytesIO()
        hdr = "CTL%s\n" % self.shop_code.upper()
        hdr = _process_line(hdr)
        ftxt.write(hdr.encode())
        #header1
        partner_ref = self.partner_id.ref[:4].upper() if self.partner_id.ref \
            else ''
        post_date = self.posting_date.strftime('%d%m%Y')
        tp_loc = "" if not self.third_party_location else self.third_party_location.upper()
        hd1 = "HD1%s%s%s%s%s%s%s%s\n" % (
            partner_ref, self.shop_code.upper(), post_date, self.container_label[:11].upper(),
            self.mode_id.code.upper(), self.repair_cause, tp_loc, self.wo_type)
        hd1 = _process_line(hd1)
        ftxt.write(hd1.encode())
        part = []
        #header2
        vendor_ref = self.reference[:10] if self.reference else ''
        #convert untaxed amount into string
        if self.amount_untaxed_estimation:
            header = str(int(self.amount_untaxed_estimation))
            dec = str(round(self.amount_untaxed_estimation - int(self.amount_untaxed_estimation),2))[1:].split('.')[1]
        else:
            header = "0"
            dec = "00"
        while len(header) < 10:
            header = "0%s" % (header)
        while len(dec) < 2:
            dec = "%s0" % (dec)
        untax = "%s%s" % (header, dec)
        hd2 = "HD2                          %s0000000000000000%s\n" % (
            vendor_ref, untax)
        hd2 = _process_line(hd2)
        ftxt.write(hd2.encode())
        #remark
        notes = self.internal_notes[:77].upper() if self.internal_notes \
            else ''
        remark = "RMK%s\n" % (notes)
        remark = _process_line(remark)
        ftxt.write(remark.encode())
        for line in self.estimation_line_ids.filtered(lambda r: r.approved):
            #repair
            damage_id = line.repair_damage_id
            #convert material price into string
            if line.material_price:
                material_price_divided = line.material_price
                if line.quantity and line.quantity > 0:
                    material_price_divided = line.material_price / line.quantity
                header = str(int(material_price_divided))
                dec = str(round(material_price_divided - int(material_price_divided),2))[1:].split('.')[1]
            else:
                header = "0"
                dec = "00"
            while len(header) < 10:
                header = "0%s" % (header)
            while len(dec) < 2:
                dec = "%s0" % (dec)
            mprice = "%s%s" % (header, dec)
            #convert sts into string
            if line.sts:
                sts_divided = line.sts
                if line.quantity and line.quantity > 0:
                    sts_divided = line.sts / line.quantity
                header = str(int(sts_divided))
                dec = str(round(sts_divided - int(sts_divided),2))[1:].split('.')[1]
            else:
                header = "00"
                dec = "00"
            while len(header) < 2:
                header = "0%s" % (header)
            while len(dec) < 2:
                dec = "%s0" % (dec)
            sts = "%s%s" % (header, dec)
            repair_code = line.tariff_line_id.repair_code[:6] \
                if line.tariff_line_id.repair_code else ""

            repair_qty = str(int(round(line.quantity, 0)))
            while len(repair_qty) < 3:
                repair_qty = "0%s" % (repair_qty)
            repln = "RPR%s  %s%s%s%s%s%s\n" % (
                damage_id.damage_type_id.code[:2].upper(),
                repair_code.upper(), damage_id.location_id.code[:4].upper(),
                repair_qty, mprice, sts,
                line.repair_damage_id.third_party_indicator.upper())
            repln = _process_line(repln)
            ftxt.write(repln.encode())
            lnpart = line.tariff_line_id.material_line_ids.filtered(
                lambda r: r.product_id.part_number_generation)
            for spart in lnpart:
                part.append({'product_id': spart.product_id,
                             'quantity': spart.quantity * line.quantity})
        for line in part:
            #convert parts into string
            if line.get('quantity'):
                header = str(int(line.get('quantity')))
                dec = str(round(line.get('quantity') - int(line.get('quantity')),2))[1:].split('.')[1]
            else:
                header = "00"
                dec = "0"
            while len(header) < 2:
                header = "0%s" % (header)
            prt = "PRT%s%s\n" % (header[-2:], dec)
            prt = _process_line(prt)
            ftxt.write(prt.encode())
        ftxt = base64.encodestring(ftxt.getvalue())
        mail_template = self.env.ref('ecs_repair.email_template_edi',
                                     raise_if_not_found=False)
        if mail_template:
            fname = '%s.txt' % self.container_label
            subject = "%s_%s" % (self.container_label, self.reference)
            try:
                body = cropped and (_("Attention! The lines in this file were cropped to the length of %d characters. Some information may have been lost.") % cropped) or ""
                mail_template.sudo().send_mail(
                    self.id, force_send=True,
                    email_values={'email_to': self.partner_id.edi_email_file,
                                  'subject': subject,
                                  'body': body,
                                  'attachments': [(fname, ftxt)]})
            except:
                _logger.info('Fail to send EDI file mail')

    def action_submit(self):
        """ Change state repair order into submitted """

        self.ensure_one()
        self.write({'posting_date': fields.Datetime.now(),
                    'state': 'submitted'})
        if self.partner_id.edi_partner:
            self._send_image_files()
            self._send_edi_file()

    def _prepare_repair_lines(self):
        """ Generate value for repair lines """

        rep_line = []
        for line in self.estimation_line_ids.filtered(lambda r: r.approved):
            tariff = line.tariff_line_id
            component_line = []
            for mat in tariff.material_line_ids:
                qty = mat.quantity
                vals = {'product_id': mat.product_id.id,
                        'name': mat.product_id.name,
                        'quantity': qty,
                        'actual_quantity': qty,
                        'src_location_id': self.repair_operation_id.default_location_src_id.id,
                        'uom_id': mat.uom_id.id}
                component_line.append((0, 0, vals))
            dimension = "%s x %s" % (tariff.width, tariff.length)
            vals = {'seq_num': line.seq_num,
                    'name': line.name,
                    'quantity': line.quantity,
                    'sts': line.sts * line.quantity,
                    'component_id': tariff.component_id.id,
                    'location_id': tariff.location_id.id,
                    'damage_type_id': tariff.damage_type.id,
                    'repair_type_id': tariff.repair_type_id.id,
                    'dimension': dimension,
                    'tariff_line_id': tariff.id,
                    'material_line_ids': component_line}
            rep_line.append((0, 0, vals))
        if not rep_line:
            raise UserError(_("There is no approved estimation line!"))
        return rep_line

    def action_server_approve(self):
        for order in self:
            if order.state != 'submitted':
                raise UserError(_("One of the EORs selected is not in state Submitted"))
            order.action_approve()

    def action_approve(self):
        """ Change state into approved """

        self.ensure_one()
        #validate single tax
        taxes = self.estimation_line_ids.filtered(lambda r: r.approved).mapped('tax_ids')
        no_tax = self.estimation_line_ids.filtered(lambda r: r.approved and not r.tax_ids)
        if len(taxes) > 1 or no_tax:
            raise UserError(_("Can only proceed estimation with similar tax!"))
        repair_lines = self._prepare_repair_lines()
        return self.write({'state': 'approved',
                           'approval_date': fields.Datetime.now(),
                           'work_order_line_ids': repair_lines})

    def action_reject(self):
        """ Change state into reject """

        self.ensure_one()
        return self.write({'state': 'reject'})

    def action_reestimate(self):
        """ Return state into submitted """

        self.ensure_one()
        if self.partner_id.edi_partner:
            self._send_image_files()
            self._send_edi_file()
        return self.write({'state': 'submitted'})

    def action_confirm_repair(self):
        """ Change state into planned """

        self.ensure_one()

        # TODO: may be removed in the future
        # surveyor = self.surveyor_id
        # planned_date = self.planned_date
        # unassigned = self.work_order_line_ids.filtered(
        #     lambda r: r.state == 'new' or not \
        #     (r.mechanic1_id or r.mechanic2_id or r.mechanic3_id or r.mechanic4_id))
        # if self.state == 'approved' and all([surveyor, planned_date, unassigned]):

        #if not self.planned_date or not self.surveyor_id:
            #raise UserError(_("Can't confirm until planned date and surveyor filled!"))
        
        # self.work_order_line_ids.write({'state':'in_progress'})
        if self.state == 'approved':
            self.write({'state': 'planned'})
        else:
            raise UserError(_("Can only confirm approved repair with surveyor " \
                              "& planned date assigned and having no work order in new state!"))
        
        for work_order_line_id in self.work_order_line_ids.filtered(lambda wol: wol.state != 'cancel'):
            work_order_line_id.action_start_repair()

        return True

    def action_review_order(self):
        """ Return state into to be invoiced """

        self.ensure_one()
        return self.write({'state': '2binvoiced'})

    def action_complete_repair(self):
        for order in self:
            if order.state != 'to_complete':
                raise UserError(_("One of the EORs selected is not in state Review to Complete."))

            done_time = fields.Datetime.now()
            order.write({'completion_date': done_time})
            order.action_review_order()

    def action_pass_qc(self):
        for line in self.work_order_line_ids.filtered(lambda wo: wo.state != 'cancel'):
            # line.validation_mechanic()
            line.action_pass_qc()
        
        self.write({'state': 'to_complete'})

    @api.multi
    def action_mass_done_all_repair_item(self):
        """ Called from 'Done all Repair Items' button.
        Get selected EOR which has state 'In Progress' only.
        """
        for repair in self:
            if repair.state in ('in_progress'):
                for item in repair.work_order_line_ids:
                    if item.state in ('new', 'assigned'):
                        item.action_start_repair()
                    if item.state in ('in_progress', 'reword'):
                        item.action_done()

    def action_fail_qc(self):
        for line in self.work_order_line_ids.filtered(lambda wo: wo.state != 'cancel'):
            line.validation_mechanic()
    
    def recompute_update_parts_spend(self):
        for order in self:
            order.parts_line_ids = [(5,0,0)]
            for line in order.work_order_line_ids:
                line.recompute_update_parts_spend()

    @api.multi
    def action_repair_cancel(self):
        """ Inherit repair cancel """

        res = super(RepairOrder, self).action_repair_cancel()
        for rep in self.work_order_line_ids:
            rep.state = 'cancel'
        return res

    def get_default_income_account(self):
        """ Get company default income account """

        #get company default income account
        ln_account = self.env.ref('account.field_account_invoice_line__account_id')
        sales_account = self.env['ir.property'].search_read(
            domain=[('fields_id', '=', ln_account.id),
                    '|', ('company_id', '=', self._context.get('company', False)),
                    ('company_id', '=', False)],
            fields=['value_reference'], limit=1)
        sales_account = sales_account[0].get('value_reference') if sales_account else False
        sales_account = int(sales_account.split(',')[1]) if sales_account else False
        if sales_account:
            sales_account = self.env['account.account'].search_read(
                domain=[('id', '=', sales_account)], fields=['id'])
            sales_account = sales_account[0].get('id') if sales_account else False
        return sales_account

    @api.multi
    def action_generate_invoice(self):
        """ Generate Invoice """

        for repair in self:
            if not repair.partner_id.property_account_receivable_id:
                raise UserError(_('No account defined for partner "%s".') % repair.partner_id.name)
            sales_account = self.with_context(
                company=repair.company_id.id).get_default_income_account()
            if not sales_account:
                raise UserError(_('No default income account defined for company "%s".') \
                                % repair.company_id.name)
            if not repair.estimation_line_ids.filtered(lambda r: r.approved):
                raise UserError(_('No lines to invoiced!'))
            price = 0.0
            for line in repair.estimation_line_ids.filtered(lambda r: r.approved):
                price += line.quantity * (line.labour_price + line.material_price)
            taxes = repair.estimation_line_ids.filtered(lambda r: r.approved).mapped('tax_ids')
            inv_ln = {'name': 'Dịch vụ sửa chữa',
                      'origin': repair.name,
                      'account_id': sales_account,
                      'quantity': 1,
                      'invoice_line_tax_ids': [(6, 0, [tid.id for tid in taxes if taxes])],
                      'price_unit': price,
                      'price_subtotal': 1 * price}
            invoice = self.env['account.invoice'].create({
                'name': repair.name,
                'origin': repair.name,
                'type': 'out_invoice',
                'account_id': repair.partner_id.property_account_receivable_id.id,
                'partner_id': repair.partner_invoice_id.id or repair.partner_id.id,
                'currency_id': repair.tariff_id.currency_id.id,
                'comment': repair.quotation_notes,
                'fiscal_position_id': repair.partner_id.property_account_position_id.id,
                'invoice_line_ids': [(0, 0, inv_ln)]})
            invoice.compute_taxes()
            repair.write({'invoiced': True,
                          'state': 'draft_invoice',
                          'invoice_id': invoice.id})
        return True

    def update_invoice_status(self, origin):
        """ Change state based on action invoice """

        origin = origin.replace(', ', ',').split(',')
        for seq in origin:
            repair = self.search([('name', '=', seq)], limit=1)
            if repair and repair.state == 'draft_invoice':
                nstate = '2binvoiced' if self._context.get('removed') \
                    else 'invoiced'
                repair.write({'state': nstate})

    def action_close_order(self):
        """ Return state into done """

        self.ensure_one()
        return self.write({'state': 'done'})

    def set_damage_sequence(self, vals, ln_seq=0):
        """ Set Sequence Of Damage Lines """

        new_line = [x for x in vals.get('damage_line_ids') if len(x) == 3 and x[0] == 0]
        if not new_line:
            return vals
        dmg_line = sorted(new_line, key=lambda k: ('seq_num' in k[2], k[2].get('seq_num')))
        img_num = 1
        idx = 1 if not ln_seq else ln_seq
        cont = vals.get('container_label') or self.container_label
        for line in dmg_line:
            if 'evidence_1_file' in line[2] and line[2].get('evidence_1_file'):
                fname = "%s(%s).%s" % (
                    cont, img_num, line[2].get('evidence_1_file').rsplit('.')[1])
                img_num += 1
                line[2]['evidence_1_file'] = fname
            if 'evidence_2_file' in line[2] and line[2].get('evidence_2_file'):
                fname = "%s(%s).%s" % (
                    cont, img_num, line[2].get('evidence_2_file').rsplit('.')[1])
                img_num += 1
                line[2]['evidence_2_file'] = fname
            if 'evidence_3_file' in line[2] and line[2].get('evidence_3_file'):
                fname = "%s(%s).%s" % (
                    cont, img_num, line[2].get('evidence_3_file').rsplit('.')[1])
                img_num += 1
                line[2]['evidence_3_file'] = fname
            if 'evidence_4_file' in line[2] and line[2].get('evidence_4_file'):
                fname = "%s(%s).%s" % (
                    cont, img_num, line[2].get('evidence_4_file').rsplit('.')[1])
                img_num += 1
                line[2]['evidence_4_file'] = fname
            if 'evidence_5_file' in line[2] and line[2].get('evidence_5_file'):
                fname = "%s(%s).%s" % (
                    cont, img_num, line[2].get('evidence_5_file').rsplit('.')[1])
                img_num += 1
                line[2]['evidence_5_file'] = fname
            line[2]['seq_num'] = idx
            idx += 1
        if idx > 1:
            vals['line_sequence'] = idx
        if img_num > 1:
            vals['image_sequence'] = img_num
        return vals

    def update_image_sequence(self):
        """ Update Image Sequence """

        img_num = 1
        dmg_vals = []
        for line in self.damage_line_ids:
            ln_vals = {}
            if line.evidence_1_file:
                fname = "%s(%s).%s" % (
                    self.container_label, img_num, line.evidence_1_file.rsplit('.')[1])
                img_num += 1
                ln_vals['evidence_1_file'] = fname
            if line.evidence_2_file:
                fname = "%s(%s).%s" % (
                    self.container_label, img_num, line.evidence_2_file.rsplit('.')[1])
                img_num += 1
                ln_vals['evidence_2_file'] = fname
            if line.evidence_3_file:
                fname = "%s(%s).%s" % (
                    self.container_label, img_num, line.evidence_3_file.rsplit('.')[1])
                img_num += 1
                ln_vals['evidence_3_file'] = fname
            if line.evidence_4_file:
                fname = "%s(%s).%s" % (
                    self.container_label, img_num, line.evidence_4_file.rsplit('.')[1])
                img_num += 1
                ln_vals['evidence_4_file'] = fname
            if line.evidence_5_file:
                fname = "%s(%s).%s" % (
                    self.container_label, img_num, line.evidence_5_file.rsplit('.')[1])
                img_num += 1
                ln_vals['evidence_5_file'] = fname
            if ln_vals:
                dmg_vals.append((1, line.id, ln_vals))
        if dmg_vals:
            self.write({'damage_line_ids': dmg_vals})

    @api.model
    def create(self, vals):
        """ Inherit create """

        if vals.get('container_label'):
            vals['container_label'] = vals.get('container_label', '').upper()
            self.validation_container_label(vals['container_label'])
        if vals.get('damage_line_ids'):
            vals = self.set_damage_sequence(vals)
        res = super(RepairOrder, self).create(vals)
        if not res.return_repair_operation_id:
            raise UserError(_("There is no return repair operation defined for %s. " \
                              "Please contact administrator!" % res.warehouse_id.name))
        if not res.repair_operation_id:
            raise UserError(_("There is no repair operation defined for %s. " \
                              "Please contact administrator!" % res.warehouse_id.name))
        return res

    @api.multi
    def write(self, vals):
        """ Inherit write """

        if 'container_label' in vals and vals.get('container_label'):
            vals['container_label'] = vals.get('container_label', '').upper()
            self.validation_container_label(vals['container_label'])
        for rep in self:
            if vals.get('damage_line_ids'):
                vals = rep.set_damage_sequence(vals, rep.line_sequence)
            incomplete = rep.work_order_line_ids.filtered(
                lambda r: r.qc_status != 'passed' and r.state != 'cancel')
            if vals.get('qc_staff_id') and not incomplete and rep.state == 'in_progress':
                vals['state'] = 'to_review'
        res = super(RepairOrder, self).write(vals)
        for order in self:
            if not order.return_repair_operation_id:
                raise UserError(_("There is no return repair operation defined for %s. " \
                                  "Please contact administrator!" % order.warehouse_id.name))
            if not order.repair_operation_id:
                raise UserError(_("There is no repair operation defined for %s. " \
                                  "Please contact administrator!" % order.warehouse_id.name))
            key = ['evidence_1', 'evidence_2', 'evidence_3', 'evidence_4',
                   'evidence_5']
            #update image sequence
            if order.damage_line_ids and not self._context.get('rename_img') \
                and vals.get('damage_line_ids') \
                and [x for x in vals.get('damage_line_ids') if vals.get('damage_line_ids') \
                     and x[0] in [0, 1] and [y for y in key if key and y in x[2]]]:
                order.with_context(rename_img=True).update_image_sequence()            
        return res

    @api.multi
    def unlink(self):
        """ Inherit unlink """

        for order in self:
            if order.state != 'draft':
                raise UserError(_("Can only delete repair orders in draft state!"))
        return super(RepairOrder, self).unlink()

    def action_resend_edi_images(self):
        """ Action resend EDI + images """
        if self.partner_id.edi_partner:
            self._send_edi_file()
            self._send_image_files()

    def action_resend_images(self):
        """ Action resend images """
        if self.partner_id.edi_partner:
            self._send_image_files()

    def action_resend_edifile(self):
        """ Action resend images """
        if self.partner_id.edi_partner:
            self._send_edi_file()


class RepairOrderDamage(models.Model):
    """ Repair Order Damage Line """

    _name = 'repair.order.damage'
    _description = 'Repair Order Damage'

    repair_order_id = fields.Many2one('repair.order',
                                      ondelete='cascade', index=True)
    name = fields.Char('Combined Code', compute='_compute_combined_name', store=True)
    component_id = fields.Many2one('repair.component', string="Component", required=True)
    container_label = fields.Char(string="Container ID", related='repair_order_id.container_label')
    damage_type_id = fields.Many2one('damage.type', string="Damage", required=True)
    description = fields.Text()
    edi_partner = fields.Boolean(related='repair_order_id.partner_id.edi_partner')
    estimation_line_ids = fields.One2many('repair.order.estimation',
                                          'repair_damage_id', copy=False)
    evidence_1 = fields.Binary()
    evidence_1_file = fields.Char()
    evidence_2 = fields.Binary()
    evidence_2_file = fields.Char()
    evidence_3 = fields.Binary()
    evidence_3_file = fields.Char()
    evidence_4 = fields.Binary()
    evidence_4_file = fields.Char()
    evidence_5 = fields.Binary()
    evidence_5_file = fields.Char()
    
    length = fields.Char()
    location_id = fields.Many2one('repair.location', string="Location", required=True)
    mode_id = fields.Many2one('repair.mode', related='repair_order_id.mode_id')
    quantity = fields.Integer()
    repair_type_id = fields.Many2one('repair.types', string="Repair Code", required=True)
    seq_num = fields.Integer(string='S/N')
    tariff_id = fields.Many2one('repair.tariff', related='repair_order_id.tariff_id')
    third_party_indicator = fields.Selection([('T', 'Third Party'),
                                              ('W', 'Wear and Tear')])
    width = fields.Char()
    public_ids = fields.One2many('public.document', 'repair_line_id', copy=False)
    image_quantity = fields.Integer(default=0, copy=False, compute='_compute_image_quantity')

    @api.depends('public_ids')
    def _compute_image_quantity(self):
        for line in self:
            i = 0
            for doc in line.public_ids.filtered(lambda p: p.document):
                i += 1
            
            line.image_quantity = i

    def wizard_uploader(self):
        view_id = self.env.ref('ecs_repair.view_wizard_uploader_form')
        wizard_id = self.env['wizard.uploader'].create({'repair_line_id': self.id, 'repair_order_id': self.repair_order_id.id})

        return {
            'name': _('Upload Document'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.uploader',
            'res_id': wizard_id.id,
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'context': self.env.context,
        }
    
    def action_show_documents(self):
        self.ensure_one()

        view = self.env.ref('ecs_repair.view_repair_order_damage_form_upload')
        return {
            'name': _('Upload Documents'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'repair.order.damage',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': {},
        }

    @api.constrains('length')
    def _constrains_length(self):
        """ Constrains Length """

        if self.length:
            try:
                int(self.length)
            except Exception:
                raise UserError(_("Length must be numeric value!"))

    @api.constrains('width')
    def _constrains_width(self):
        """ Constrains Width """

        if self.width:
            try:
                int(self.width)
            except Exception:
                raise UserError(_("Width must be numeric value!"))

    @api.multi
    @api.depends('component_id', 'location_id', 'damage_type_id',
                 'repair_type_id', 'length', 'width')
    def _compute_combined_name(self):
        """ Combining name from listed code """

        for line in self:
            if line.component_id and line.location_id and line.damage_type_id \
                and line.repair_type_id:
                dimension = "%s x %s" % (line.length or '', line.width or '')
                line.name = (str(line.component_id.code) + '|' +
                             str(line.location_id.code) + '|' +
                             str(line.damage_type_id.code) + '|' +
                             str(line.repair_type_id.code) + '|' +
                             dimension)

    @api.onchange('component_id', 'location_id', 'damage_type_id')
    def _onchange_domain(self):
        """ Set domain for location, damage and repair type """

        for damage in self:
            # location domain
            if damage.component_id:
                loc = self.env['repair.location'].search_read(
                    domain=[('component_ids', 'in', [damage.component_id.id])],
                    fields=['id'])
                loc = [x.get('id') for x in loc if loc]
                loc = [('id', 'in', loc)] if loc else loc
            else:
                loc = [('id', 'in', [])]
            # damage type domain
            com_domain = [('component_ids', 'in', [damage.component_id.id])] \
                if damage.component_id else [('component_ids', 'in', [])]
            loc_domain = [('location_ids', 'in', [damage.location_id.id])] \
                if damage.location_id else [('location_ids', 'in', [])]
            dam_domain = com_domain + loc_domain
            dam = self.env['damage.type'].search_read(
                domain=dam_domain, fields=['id'])
            dam = [x.get('id') for x in dam if dam]
            dam = dam if not dam and damage.component_id and damage.location_id \
                else [('id', 'in', dam)]
            # repair type domain
            dmg_domain = [('damage_ids', 'in', [damage.damage_type_id.id])] \
                if damage.damage_type_id else [('damage_ids', 'in', [])]
            rep_domain = dam_domain + dmg_domain
            rep = self.env['repair.types'].search_read(
                domain=rep_domain, fields=['id'])
            rep = [x.get('id') for x in rep if rep]
            rep = rep if not rep and damage.component_id and damage.location_id and \
                damage.damage_type_id else [('id', 'in', rep)]
            return {'domain': {'location_id': loc,
                               'damage_type_id': dam,
                               'repair_type_id': rep}}

    def _prepare_estimation_line(self, vals, repair_order, tariff):
        """ Preparing value for estimation line """

        res = []
        component = self.env['repair.component'].search_read(
            domain=[('id', '=', vals.get('component_id'))],
            fields=['code'])
        location = self.env['repair.location'].search_read(
            domain=[('id', '=', vals.get('location_id'))],
            fields=['code'])
        damage_type = self.env['damage.type'].search_read(
            domain=[('id', '=', vals.get('damage_type_id'))],
            fields=['code'])
        repair_type = self.env['repair.types'].search_read(
            domain=[('id', '=', vals.get('repair_type_id'))],
            fields=['code'])
        dimension = "%s x %s" % (vals.get('length') or '0', vals.get('width') or '0')
        name = '%s|%s|%s|%s|%s' % (
            component[0].get('code'), location[0].get('code'),
            damage_type[0].get('code'), repair_type[0].get('code'), dimension)
        domain = [('tariff_id', '=', tariff), ('quantity', '=', vals.get('quantity')),
                  ('name', '=', name)]
        tariff_line = self.env['repair.tariff.line'].search(
            domain, limit=1)
        if tariff_line:
            taxes = [tax_id.id for tax_id in tariff_line.tax_ids if tariff_line.tax_ids]
            res = [(0, 0, {'seq_num': vals.get('seq_num'),
                           'quantity': vals.get('quantity'),
                           'repair_order_id': repair_order,
                           'labour_price': tariff_line.labour_price,
                           'repair_code': tariff_line.repair_code,
                           'tariff_line_id': tariff_line.id,
                           'tax_ids': [(6, 0, taxes)],
                           'material_price': tariff_line.material_price,
                           'sts': tariff_line.sts})]
        else:
            raise ValidationError(
                _("Tariff line for %s with quantity %s can not be found!" \
                  % (name, vals.get('quantity'))))
        return res

    def resize_image(self, vals):
        """ Resize Image Using Standard of Erria """

        if 'evidence_1' in vals and vals.get('evidence_1'):
            image = ustr(vals.get('evidence_1', '')).encode('utf-8')
            vals['evidence_1'] = image_resize_image(image, size=(448, 336))
        if 'evidence_2' in vals and vals.get('evidence_2'):
            image = ustr(vals.get('evidence_2', '')).encode('utf-8')
            vals['evidence_2'] = image_resize_image(image, size=(448, 336))
        if 'evidence_3' in vals and vals.get('evidence_3'):
            image = ustr(vals.get('evidence_3', '')).encode('utf-8')
            vals['evidence_3'] = image_resize_image(image, size=(448, 336))
        if 'evidence_4' in vals and vals.get('evidence_4'):
            image = ustr(vals.get('evidence_4', '')).encode('utf-8')
            vals['evidence_4'] = image_resize_image(image, size=(448, 336))
        if 'evidence_5' in vals and vals.get('evidence_5'):
            image = ustr(vals.get('evidence_5', '')).encode('utf-8')
            vals['evidence_5'] = image_resize_image(image, size=(448, 336))
        return vals

    @api.model
    def create(self, vals):
        """ Extend create """

        # auto generate estimation line
        gen_date = fields.Datetime.now()
        tariff = vals.get('tariff_id') or self._context.get('tariff_id') or False
        if not tariff and vals.get('repair_order_id'):
            tariff = self.env['repair.order'].browse(vals.get('repair_order_id')).tariff_id.id
        if vals.get('repair_order_id') and tariff:
            est_line = self._prepare_estimation_line(vals, vals.get('repair_order_id'), tariff)
            vals['estimation_line_ids'] = est_line
            vals['length'] = '0' if 'length' not in vals or not vals.get('length') \
                else vals.get('length')
            vals['width'] = '0' if 'width' not in vals or not vals.get('width') \
                else vals.get('width')
        vals = self.resize_image(vals)
        res = super(RepairOrderDamage, self).create(vals)
        res.repair_order_id.action_generate_image_sequence()
        res.repair_order_id.action_sn_sequence()
        if res.estimation_line_ids and not res.repair_order_id.estimation_date:
            res.repair_order_id.estimation_date = gen_date
        return res

    @api.multi
    def write(self, vals):
        """ Inherit Write """

        if 'length' in vals and not vals.get('length'):
            vals['length'] = '0'
        if 'width' in vals and not vals.get('width'):
            vals['width'] = '0'
        vals = self.resize_image(vals)
        res = super(RepairOrderDamage, self).write(vals)
        self.repair_order_id.action_generate_image_sequence()
        #update estimation
        key = ['component_id', 'location_id', 'damage_type_id', 'repair_type_id', 'tariff_id',
               'quantity', 'width', 'length']
        if [x for x in key if vals and key and x in vals]:
            for line in self:
                domain = [('tariff_id', '=', line.tariff_id.id), ('quantity', '=', line.quantity),
                          ('name', '=', line.name)]
                tariff_line = self.env['repair.tariff.line'].search(
                    domain, limit=1)
                if tariff_line and line.estimation_line_ids:
                    taxes = [tax_id.id for tax_id in tariff_line.tax_ids if tariff_line.tax_ids]
                    est_vals = {'seq_num': line.seq_num,
                                'quantity': line.quantity,
                                'labour_price': tariff_line.labour_price,
                                'repair_code': tariff_line.repair_code,
                                'tariff_line_id': tariff_line.id,
                                'tax_ids': [(6, 0, taxes)],
                                'material_price': tariff_line.material_price,
                                'sts': tariff_line.sts}
                    line.estimation_line_ids.write(est_vals)
                elif not tariff_line:
                    raise ValidationError(
                        _("Tariff line for %s with quantity %s can not be found!" \
                          % (line.name, line.quantity)))
        return res


class RepairOrderEstimation(models.Model):
    """ Repair Order Estimation """

    _name = 'repair.order.estimation'
    _description = 'Repair Order Estimation'

    @api.depends('labour_price', 'material_price', 'repair_order_id')
    def _compute_amount(self):
        """ Compute amount in line """

        for line in self:
            price_unit = line.labour_price + line.material_price
            partner = line.repair_order_id.partner_id if line.repair_order_id.partner_id \
                else None
            taxes = line.tax_ids.compute_all(
                price_unit,
                line.repair_order_id.tariff_id.currency_id, 1.0, None, partner)
            line.update(
                {'price_subtotal': price_unit,
                 'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                 'price_total': taxes['total_included']})

    @api.depends('sts', 'tariff_line_id')
    def _compute_labour_price(self):
        """ Compute Labout Price """

        for line in self:
            line.update({'labour_price': line.sts * line.tariff_line_id.tariff_id.sts_value})
            #line.labour_price = line.sts * line.tariff_line_id.tariff_id.sts_value

    repair_order_id = fields.Many2one('repair.order', required=True,
                                      ondelete='cascade', index=True)
    repair_damage_id = fields.Many2one('repair.order.damage', required=True,
                                       ondelete='cascade', index=True)
    name = fields.Char('Combined Code', related='repair_damage_id.name', store=True)
    approved = fields.Boolean(string='Is Approved', default=True)
    currency_id = fields.Many2one('res.currency',
                                  related='repair_order_id.currency_id')
    labour_price = fields.Monetary(
        'Labour Cost', compute='_compute_labour_price', store=True)
    material_price = fields.Monetary()
    price_subtotal = fields.Monetary('Subtotal', compute='_compute_amount', store=True)
    price_tax = fields.Monetary(compute='_compute_amount', store=True)
    price_total = fields.Monetary(compute='_compute_amount', store=True)
    quantity = fields.Integer()
    repair_code = fields.Char()
    seq_num = fields.Integer(string="S/N")
    sts = fields.Float('STS')
    tariff_line_id = fields.Many2one('repair.tariff.line')
    tax_ids = fields.Many2many('account.tax',
                               'repair_estimation_tax_rel',
                               'estimation_id', 'tax_id')


    @api.model
    def create(self, vals):
        res = super(RepairOrderEstimation, self).create(vals)
        res.repair_order_id.action_sn_estimation()
        return res
        

class RepairOrderParts(models.Model):
    """ Repair Order Parts """

    _name = 'repair.order.parts'
    _description = 'Repair Order Parts Spent'

    @api.depends('purchase_price', 'actual_quantity')
    def _compute_price(self):
        """ Compute price """

        for line in self:
            total = line.actual_quantity * line.purchase_price
            line.update({'purchase_price_subtotal': total})

    repair_order_id = fields.Many2one('repair.order', required=True,
                                      ondelete='cascade', index=True)
    name = fields.Char()
    actual_quantity = fields.Float()
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.ref('base.main_company').currency_id)
    product_id = fields.Many2one('product.product')
    purchase_price = fields.Float()
    purchase_price_subtotal = fields.Float(compute='_compute_price', store=True)
    quantity = fields.Float('Planned Quantity')
    return_required = fields.Boolean(related='product_id.return_required')
    uom_id = fields.Many2one('uom.uom')
