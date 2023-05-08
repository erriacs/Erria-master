'''repair.order.report'''
from odoo import api, fields, models, tools


class RepairOrderReport(models.Model):
    '''new model repair.order.report'''
    _name = 'repair.order.report'
    _description = 'Repair Order Reporting'
    _auto = False

    repair_id = fields.Many2one('repair.order', readonly=True)
    location_id = fields.Many2one('repair.location', readonly=True)
    damage_id = fields.Many2one('damage.type', readonly=True)
    repair_type_id = fields.Many2one('repair.types', readonly=True)
    component_id = fields.Many2one('repair.component', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    quantity = fields.Float(readonly=True)
    actual_quantity = fields.Float(readonly=True)
    approval_day = fields.Float(string='Days to approval', readonly=True, group_operator="avg")
    repair_day = fields.Float(string='Days to repair', readonly=True, group_operator="avg")
    finished_repair_day = fields.Float(string='Days to repair completion',
                                       readonly=True, group_operator="avg")
    planned_time = fields.Float(string='Planned Time spent (STS)', readonly=True)
    real_time = fields.Float(string='Real Time spent (STS)', readonly=True)
    container_label = fields.Char(string='Container ID', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    product_repair_id = fields.Many2one('product.product', string='Product of Repair',
                                        readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Depot', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='QC Staff', readonly=True)
    state = fields.Selection([
        ('draft', 'Quotation'), ('cancel', 'Cancelled'), ('confirmed', 'Confirmed'),
        ('under_repair', 'Under Repair'), ('ready', 'Ready to Repair'),
        ('2binvoiced', 'To be Invoiced'), ('invoice_except', 'Invoice Exception'),
        ('done', 'Repaired'), ('submitted', 'Submitted'), ('approved', 'Approved'),
        ('reject', 'Reject'), ('planned', 'Planned'), ('in_progress', 'In Progress'),
        ('to_review', 'Ready to Review'), ('draft_invoice', 'Draft Invoice'),
        ('invoiced', 'Invoiced')], readonly=True)
    repair_date = fields.Date(string='Repair Order Date', readonly=True)

    # approve, planned, in_progress, to review, draft invoice, invoice

    def _query(self, with_clause='', list_fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(ro.id) as id,
            ro.id as repair_id,
            ro.container_label as container_label,
            ro.partner_id as partner_id,
            ro.product_id as product_repair_id,
            ro.warehouse_id as warehouse_id,
            ro.qc_staff_id as employee_id,
            ro.state as state,
            ro.repair_date as repair_date,
            rwo.location_id as location_id,
            rwo.damage_type_id as damage_id,
            rwo.repair_type_id as repair_type_id,
            rwo.component_id as component_id,
            rwom.product_id as product_id,
            coalesce(rwom.quantity, 0.0) as quantity,
            coalesce(rwom.actual_quantity, 0.0) as actual_quantity,
            CASE WHEN ro.approval_date IS NOT NULL AND ro.create_date IS NOT NULL
                THEN (DATE_PART('day', (ro.approval_date::timestamp - ro.create_date::timestamp)) * 24 * 60
                    + DATE_PART('hour', (ro.approval_date::timestamp - ro.create_date::timestamp)) * 60
                    + DATE_PART('minute', (ro.approval_date::timestamp - ro.create_date::timestamp)))::float /
                    (24 * 60)
                ELSE 0.0 END AS approval_day,
            CASE WHEN ro.repair_date IS NOT NULL AND ro.approval_date IS NOT NULL
                THEN (DATE_PART('day', (ro.repair_date::timestamp - ro.approval_date::timestamp)) * 24 * 60
                    + DATE_PART('hour', (ro.repair_date::timestamp - ro.approval_date::timestamp)) * 60
                    + DATE_PART('minute', (ro.repair_date::timestamp - ro.approval_date::timestamp)))::float /
                    (24 * 60)
                ELSE 0.0 END AS repair_day,
            CASE WHEN ro.completion_date IS NOT NULL AND ro.repair_date IS NOT NULL
                THEN (DATE_PART('day', (ro.completion_date::timestamp - ro.repair_date::timestamp)) * 24 * 60
                    + DATE_PART('hour', (ro.completion_date::timestamp - ro.repair_date::timestamp)) * 60
                    + DATE_PART('minute', (ro.completion_date::timestamp - ro.repair_date::timestamp)))::float /
                    (24 * 60)
                ELSE 0.0 END AS finished_repair_day,
            rwo.sts as planned_time,
            rwo.repair_time as real_time
        """

        for field in list_fields.values():
            select_ += field

        from_ = """
            repair_order ro
                JOIN repair_work_order rwo on rwo.repair_order_id = ro.id
                JOIN repair_work_order_material rwom on rwom.work_order_id = rwo.id
            WHERE ro.state in ('approved', 'planned', 'in_progress', 'to_review', 'draft_invoice', 'invoiced', 'done')
            %s
        """ % from_clause

        groupby_ = """
            ro.id,
            ro.product_id,
            ro.warehouse_id,
            rwo.location_id,
            rwo.damage_type_id,
            rwo.repair_type_id,
            rwo.component_id,
            rwom.product_id,
            rwom.quantity,
            rwom.actual_quantity,
            rwo.sts,
            rwo.repair_time %s
        """ % groupby

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
