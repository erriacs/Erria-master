""" Purchase Order """
from datetime import datetime
from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare

from odoo.exceptions import UserError

from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseOrder(models.Model):
    """ Inherit Purchase Order """

    _inherit = 'purchase.order'

    # Make "Deliver To" not required
    picking_type_id = fields.Many2one(required=False, default=False)

    @api.multi
    def _get_destination_location(self):
        """ Overridden base not to use picking_type_id """
        self.ensure_one()
        if self.dest_address_id:
            return self.dest_address_id.property_stock_customer.id
        return False
        # return self.picking_type_id.default_location_dest_id.id

    @api.multi
    def _get_destination_location_by_picking_type(self, picking_type_id):
        """ Inspired by base _get_destination_location """
        self.ensure_one()
        if self.dest_address_id:
            return self.dest_address_id.property_stock_customer.id
        return picking_type_id.default_location_dest_id.id

    @api.model
    def _prepare_picking_by_type(self, picking_type_id):
        """ Inspired by base _prepare_picking """
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location_by_picking_type(picking_type_id),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }

    @api.multi
    def _create_picking(self):
        """ Overridden base """
        StockPicking = self.env['stock.picking']
        for order in self:
            picking_types = []
            for line in order.order_line:
                if line.product_id and line.product_id.type in ['product', 'consu']:
                    picking_types.append(line.picking_type_id)
            if not picking_types:
                return True
            for picking_type in picking_types:
                lines = order.order_line.filtered(lambda x: x.product_id.type in ('product', 'consu') and x.picking_type_id.id == picking_type.id)
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.picking_type_id.id == picking_type.id)
                if len(pickings) > 1:
                    raise UserError(_('There is more than one open transfer of the type %s.') % (picking_type))
                elif pickings:
                    picking = pickings[0]
                else:
                    res = order._prepare_picking_by_type(picking_type)
                    picking = StockPicking.create(res)
                moves = lines._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
            # if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
            #     pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            #     if not pickings:
            #         res = order._prepare_picking()
            #         picking = StockPicking.create(res)
            #     else:
            #         picking = pickings[0]
            #     moves = order.order_line._create_stock_moves(picking)
            #     moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
            #     seq = 0
            #     for move in sorted(moves, key=lambda move: move.date_expected):
            #         seq += 5
            #         move.sequence = seq
            #     moves._action_assign()
            #     picking.message_post_with_view('mail.message_origin_link',
            #         values={'self': picking, 'origin': order},
            #         subtype_id=self.env.ref('mail.mt_note').id)
        return True


class PurchaseOrderLine(models.Model):
    """ Inherit Purchase Order Line """

    _inherit = 'purchase.order.line'

    @api.model
    def _default_picking_type(self):
        res = self.order_id and self.order_id.picking_type_id or self.env['purchase.order']._default_picking_type()
        return res

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=Purchase.READONLY_STATES, required=True, default=_default_picking_type,
        help="This will determine operation type of incoming shipment")

    @api.model
    def default_get(self, default_fields):
        """ Inherit Default Get """

        res = super(PurchaseOrderLine, self).default_get(default_fields)
        res.update({'date_planned': datetime.today()})
        return res

    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Override Prepare Stock Moves to use picking_type_id for individual SO lines """
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.order_id._get_destination_location_by_picking_type(self.picking_type_id), # Changed - PCV
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.picking_type_id.id, # Changed - PCV
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'route_ids': self.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.picking_type_id.warehouse_id.route_ids])] or [], # Changed - PCV
            'warehouse_id': self.picking_type_id.warehouse_id.id, # Changed - PCV
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            # Always call '_compute_quantity' to round the diff_quantity. Indeed, the PO quantity
            # is not rounded automatically following the UoM.
            if get_param('stock.propagate_uom') != '1':
                product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = self.product_uom._compute_quantity(diff_quantity, self.product_uom, rounding_method='HALF-UP')
            res.append(template)
        return res
