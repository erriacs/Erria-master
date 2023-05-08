""" Repair Work Order """
from odoo import fields, models, api,
from odoo.exceptions import UserError


class RepairWorkOrder(models.Model):
    """ Repair Work Order """

    _name = 'repair.work.order'
    _description = 'Repair Work Order'

    @api.multi
    @api.depends('end_time')
    def _compute_repair_time(self):
        """ Compute repair time """

        for order in self:
            rep = ((order.end_time - order.start_time).total_seconds()/3600) \
                + order.rework_time if order.end_time and order.start_time \
                else 0.0
            order.repair_time = rep

    @api.depends('return_picking_ids')
    def _compute_return_picking(self):
        """ count total picking """

        for order in self:
            if order.return_picking_ids:
                order.update({'return_picking_counts': len(self.return_picking_ids)})
            else:
                order.update({'return_picking_counts': 0})

    @api.depends('picking_ids')
    def _compute_picking(self):
        """ count total picking """

        for order in self:
            if order.picking_ids:
                order.update({'picking_counts': len(self.picking_ids)})
            else:
                order.update({'picking_counts': 0})

    repair_order_id = fields.Many2one('repair.order', required=True,
                                      ondelete='cascade', index=True)
    name = fields.Char('Combined Code')
    attachment = fields.Binary()
    component_id = fields.Many2one('repair.component', required=True)
    container_label = fields.Char(string="Container ID",
                                  related='repair_order_id.container_label',
                                  store=True)
    damage_type_id = fields.Many2one('damage.type', required=True)
    dimension = fields.Char()
    end_time = fields.Datetime(copy=False)
    height = fields.Float()
    location_id = fields.Many2one('repair.location', required=True)
    material_line_ids = fields.One2many('repair.work.order.material', 'work_order_id',
                                        domain=[('product_id.type', '=', 'product')])
    mechanic1_id = fields.Many2one('hr.employee', string="Mechanic 1", copy=False)
    mechanic2_id = fields.Many2one('hr.employee', string="Mechanic 2", copy=False)
    mechanic3_id = fields.Many2one('hr.employee', string="Mechanic 3", copy=False)
    mechanic4_id = fields.Many2one('hr.employee', string="Mechanic 4", copy=False)
    note = fields.Text()
    partner_id = fields.Many2one('res.partner',
                                 string='Customer',
                                 related='repair_order_id.partner_id')
    picking_counts = fields.Integer(compute='_compute_picking')
    picking_ids = fields.One2many('stock.picking', 'work_order_id', copy=False)
    qc_status = fields.Selection([('passed', 'Passed'),
                                  ('failed', 'Failed')],
                                 copy=False)
    qc_time = fields.Datetime(copy=False)
    quantity = fields.Float()
    repair_time = fields.Float("Actual Repair Time (hrs)",
                               compute="_compute_repair_time", store=True)
    repair_type_id = fields.Many2one('repair.types', required=True)
    return_picking_counts = fields.Integer(compute='_compute_return_picking')
    return_picking_ids = fields.One2many('stock.picking', 'return_work_order_id',
                                         copy=False)
    rework_date = fields.Datetime(copy=False)
    rework_required = fields.Boolean(copy=False)
    rework_time = fields.Float(default=0.0, copy=False)
    seq_num = fields.Integer(string="S/N")
    start_time = fields.Datetime(copy=False)
    state = fields.Selection([('new', 'New'),
                              ('assigned', 'Assigned'),
                              ('in_progress', 'In Progress'),
                              ('done', 'Done'),
                              ('rework', 'Rework'),
                              ('cancel', 'Cancelled')],
                             default='new', copy=False)
    sts = fields.Float('STS')
    tariff_line_id = fields.Many2one('repair.tariff.line')
    warehouse_id = fields.Many2one('stock.warehouse',
                                   string='Depot',
                                   related='repair_order_id.warehouse_id')
    width = fields.Float()
    wh_view_location_id = fields.Many2one('stock.location', related='warehouse_id.view_location_id')

    def _action_create_picking(self):
        """ action to create picking """

        date = fields.Datetime.now()
        lines = []
        picking_type = self.repair_order_id.repair_operation_id
        for line in self.material_line_ids:
            vals = (0, 0, {
                'company_id': self.env.user.company_id.id,
                'date': date,
                'date_expected': date,
                'picking_type_id': picking_type.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'location_id': line.src_location_id.id,
                'product_id': line.product_id.id,
                'product_uom': line.uom_id.id,
                'product_uom_qty': line.quantity,
                'name': self.name,
            })
            lines.append(vals)
        if lines:
            mechanic = self.mechanic1_id.id or self.mechanic2_id.id \
                or self.mechanic3_id.id or self.mechanic4_id.id
            pick_vals = {
                'employee_id': mechanic,
                'company_id': self.env.user.company_id.id,
                'move_type': 'direct',
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'move_ids_without_package': lines,
                'work_order_id': self.id,
            }
            return self.env['stock.picking'].create(pick_vals)

    def _action_return_repair_picking(self):
        """ create return repair picking """

        date = fields.Datetime.now()
        lines = []
        picking_type = self.repair_order_id.return_repair_operation_id
        for line in self.tariff_line_id.material_line_ids.filtered(
                lambda r: r.product_id.type == 'product' and r.product_id.return_required):

            vals = (0, 0, {
                'company_id': self.env.user.company_id.id,
                'date': date,
                'date_expected': date,
                'picking_type_id': picking_type.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'location_id': picking_type.default_location_src_id.id,
                'product_id': line.product_id.id,
                'product_uom': line.uom_id.id,
                'product_uom_qty': line.quantity * self.quantity,
                'name': self.name,
            })
            lines.append(vals)
        if lines:
            mechanic = self.mechanic1_id.id or self.mechanic2_id.id \
                or self.mechanic3_id.id or self.mechanic4_id.id
            pick_vals = {
                'employee_id': mechanic,
                'company_id': self.env.user.company_id.id,
                'move_type': 'direct',
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'move_ids_without_package': lines,
                'return_work_order_id': self.id,
            }
            self.env['stock.picking'].create(pick_vals)

    # @api.multi
    # def write(self, vals):
    #     """ Inherit write """
    #     # TODO: this code may be removed in the future
    #     # for order in self:
    #     #     # set state into assigned
    #     #     mechanic = order.mechanic1_id or vals.get('mechanic1_id', False) \
    #     #         or order.mechanic2_id or vals.get('mechanic2_id', False) \
    #     #         or order.mechanic3_id or vals.get('mechanic3_id', False) \
    #     #         or order.mechanic4_id or vals.get('mechanic4_id', False)
    #     #     state = order.state or vals.get('state', False)
    #     #     if mechanic and state == 'new':
    #     #         vals['state'] = 'assigned'
    #
    #     res = super(RepairWorkOrder, self).write(vals)
    #     for fin in self:
    #         # generate picking
    #
    #         # TODO: this code may be removed in the future
    #         # if fin.state == 'assigned' and not fin.return_picking_ids:
    #         #     fin._action_return_repair_picking()
    #         # if fin.state == 'assigned' and not fin.picking_ids:
    #         #     fin._action_create_picking()
    #
    #         # auto update repair order into planned
    #         unassigned = fin.repair_order_id.work_order_line_ids.filtered(
    #             lambda r: r.state == 'new')
    #
    #         # TODO: this code may be removed in the future
    #         # if fin.state == 'assigned' and not unassigned:
    #         #     if not fin.repair_order_id.planned_date or not fin.repair_order_id.surveyor_id:
    #         #         raise UserError(_("Can't change state of repair order into planned until " \
    #         #                           "planned date and surveyor filled!"))
    #         #     fin.repair_order_id.state = 'planned'
    #
    #         if fin.state == 'in_progress' and not unassigned:
    #             if not fin.repair_order_id.planned_date or not fin.repair_order_id.surveyor_id:
    #                 raise UserError(_("Can't change state of repair order into planned until " \
    #                                   "planned date and surveyor filled!"))
    #             fin.repair_order_id.state = 'planned'
    #     return res

    def action_view_return(self):
        """ action view return """

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pickings',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('return_work_order_id', '=', self.id)]
        }

    def action_view_picking(self):
        """ action view picking """

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pickings',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('work_order_id', '=', self.id)]
        }

    def action_start_repair(self):
        """ Start repair """

        self.ensure_one()
        reptime = fields.Datetime.now()
        #qcStaff = self.mechanic1_id
        if not self.repair_order_id.planned_date or not self.repair_order_id.surveyor_id:
            self.repair_order_id.planned_date = reptime
            self.repair_order_id.qc_staff_id = self.repair_order_id.surveyor_id
            self.repair_order_id.qc_staff_id = self.mechanic1_id
        #    raise UserError(_("Can't start repair, until planned date and surveyor in repair order filled!"))

        unassigned_line_ids = self.material_line_ids.filtered(lambda r: not r.src_location_id)
        if unassigned_line_ids:
            raise UserError('You must input all Source Location in Material Usage')

        #reptime = fields.Datetime.now()

        # TODO: this code may be removed in the future
        # unassigned = self.repair_order_id.work_order_line_ids.filtered(
        #     lambda r: r.state == 'new' and r.id != self.id)
        # if unassigned:
        #     raise UserError(_("Can't start repair until other work items are assigned!"))

        self.write({'start_time': reptime,
                    'state': 'in_progress'})

        if not self.return_picking_ids:
            self._action_return_repair_picking()
            self._action_create_picking()

        if self.repair_order_id.state == 'planned':
            self.repair_order_id.write({'state': 'in_progress',
                                        'repair_date': reptime})

    def validate_picking(self):
        """ Validate picking after action_done """
        # self.material_line_ids.sync_qty_move()
        for picking in self.picking_ids:
            if picking.state == 'draft':
                picking.action_confirm()

            if picking.state == 'confirmed':
                picking.action_assign()

            for move in picking.move_lines:
                move.quantity_done = move.product_uom_qty
            
            for move in picking.move_line_ids:
                move.quantity_done = move.product_uom_qty

            if picking.state in ['waiting', 'confirmed', 'assigned']:
                picking.button_validate()

    def action_done(self):
        """ Finish repair """

        self.ensure_one()
        done_time = fields.Datetime.now()
        unproceed = self.material_line_ids.filtered(
            lambda r: r.product_id.type == 'product' and r.actual_quantity <= 0.0)
        if unproceed:
            raise UserError(_("Please make sure actual quantity of repair materials " \
                              "are spent properly!"))
        vals = {'end_time': done_time,
                'rework_required': False,
                'state': 'done'}
        if self.state == 'rework' and self.rework_time == 0.0:
            rework = (done_time - self.rework_date).total_seconds()/3600
            vals.update({'rework_time': rework})
        self.write(vals)
        self.validate_picking()
        self.check_qc_staff()
        self.update_parts_spend(done_time)

    def recompute_update_parts_spend(self):
        pline = []
        for line in self.material_line_ids.filtered(
                lambda r: r.product_id.type == 'product'):
            expart = self.repair_order_id.parts_line_ids.filtered(
                lambda k, l=line: k.product_id == l.product_id)
            if expart:
                vals = {'quantity': expart[0].quantity + line.quantity,
                        'actual_quantity': expart[0].actual_quantity + line.actual_quantity}
                pline.append((1, expart[0].id, vals))
            else:
                name = '%s - %s' % (self.repair_order_id.name, line.product_id.name)
                vals = {'name': name,
                        'product_id': line.product_id.id,
                        'uom_id': line.product_id.uom_id.id,
                        'quantity': line.quantity,
                        'actual_quantity': line.actual_quantity,
                        'purchase_price': line.product_id.standard_price}
                pline.append((0, 0, vals))
        vals = {'parts_line_ids': pline}
        self.repair_order_id.write(vals)

    def action_rework(self):
        """ Start rework """

        self.ensure_one()
        self.write({'rework_date': fields.Datetime.now(),
                    'state': 'rework'})

    def check_qc_staff(self):
        if not self.repair_order_id.qc_staff_id:
            self.repair_order_id.qc_staff_id = self.mechanic1_id

    def action_fail_qc(self):
        """ Set work order into rework """

        self.ensure_one()
        self.check_qc_staff()
        self.write({'qc_time': fields.Datetime.now(),
                    'qc_status': 'failed',
                    'rework_required': True})

    def update_parts_spend(self, complete_date):
        """ Update parts spend of repair order """

        pline = []
        for line in self.material_line_ids.filtered(
                lambda r: r.product_id.type == 'product'):
            expart = self.repair_order_id.parts_line_ids.filtered(
                lambda k, l=line: k.product_id == l.product_id)
            if expart:
                vals = {'quantity': expart[0].quantity + line.quantity,
                        'actual_quantity': expart[0].actual_quantity + line.actual_quantity}
                pline.append((1, expart[0].id, vals))
            else:
                name = '%s - %s' % (self.repair_order_id.name, line.product_id.name)
                vals = {'name': name,
                        'product_id': line.product_id.id,
                        'uom_id': line.product_id.uom_id.id,
                        'quantity': line.quantity,
                        'actual_quantity': line.actual_quantity,
                        'purchase_price': line.product_id.standard_price}
                pline.append((0, 0, vals))
        vals = {'parts_line_ids': pline}
        incomplete = self.repair_order_id.work_order_line_ids.filtered(
            lambda r: not r.qc_status and r.state not in ('done', 'cancel'))

        if not incomplete:
            vals.update({'completion_date': complete_date})
            if self.repair_order_id.qc_staff_id:
                vals.update({'state': 'to_review'})
        self.repair_order_id.write(vals)

    def action_pass_qc(self):
        """ Pass QC """

        self.ensure_one()
        self.check_qc_staff()
        cmpdate = fields.Datetime.now()
        vals = {'qc_status': 'passed',
                'qc_time': cmpdate}
        if self.state != 'done':
            vals.update({'end_time': cmpdate,
                         'state': 'done'})
        self.write(vals)
        # self.update_parts_spend(cmpdate)

    def action_cancel(self):
        """ Cancel work order """

        self.ensure_one()
        if self.state != 'done':
            self.state = 'cancel'
        return True

    def validation_mechanic(self):
        if not self.mechanic1_id and not self.mechanic2_id and not self.mechanic3_id and not self.mechanic4_id:
            raise UserError(_("User can't QC, %s at least have one mechanic !") % self.display_name)
        
        return True

class RepairWorkOrderMaterial(models.Model):
    """ Repair Work Order Parts Material """

    _name = 'repair.work.order.material'
    _description = 'Repair Work Order Material'

    work_order_id = fields.Many2one('repair.work.order', required=True,
                                    ondelete='cascade', index=True)
    name = fields.Char()
    actual_quantity = fields.Float()
    product_id = fields.Many2one('product.product')
    quantity = fields.Float('Planned Quantity')
    return_required = fields.Boolean(related='product_id.return_required')
    uom_id = fields.Many2one('uom.uom')
    src_location_id = fields.Many2one('stock.location', string='Source Location')

    def update_move_location(self):
        """ Update stock move location related with this material """
        stock_move_ids = self.work_order_id.picking_ids.mapped('move_line_ids')
        if stock_move_ids:
            filtered_move_ids = stock_move_ids.filtered(
                lambda r: r.product_id == self.product_id and r.location_id != self.src_location_id)
            for move_id in filtered_move_ids:
                move_id.location_id = self.src_location_id
        
        stock_move_ids = self.work_order_id.picking_ids.mapped('move_lines')
        if stock_move_ids:
            filtered_move_ids = stock_move_ids.filtered(
                lambda r: r.product_id == self.product_id and r.location_id != self.src_location_id)
            for move_id in filtered_move_ids:
                move_id.location_id = self.src_location_id


    def write(self, vals):
        """ Extend write """
        res = super().write(vals)
        if vals.get('src_location_id'):
            self.update_move_location()
        return res


