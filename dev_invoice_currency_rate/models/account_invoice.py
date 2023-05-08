# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, tools,_

class account_invoice(models.Model):   
    
    _inherit = 'account.invoice'
    
    currency_rate = fields.Float('Rate',digits=(12, 6),readonly=True,states={'draft': [('readonly', False)]})
    is_same_currency = fields.Boolean('Same Currency')

    @api.onchange('currency_id')
    def onchage_currency_id(self):
        if self.currency_id:
            if self.currency_id.id == self.company_id.currency_id.id:
                self.is_same_currency = True
            else:
                self.is_same_currency = False
            self.currency_rate = self.currency_id.with_context(dict(self._context or {}, date=self.date_invoice)).rate
        else:
            self.currency_rate = 0.0
            
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        inv_pool=self.env['account.invoice']
        move_lines = super(account_invoice,
                           self).finalize_invoice_move_lines(move_lines)
        for move in move_lines:
            if move[2].get('invoice_id') and move[2].get('currency_id'):
                invoice_id =inv_pool.browse(move[2].get('invoice_id'))
                if invoice_id.currency_rate and move[2].get('amount_currency'):
                    amt = move[2].get('amount_currency') / invoice_id.currency_rate
                    if move[2].get('credit'):
                        move[2].update({
                            'credit':abs(amt),
                        })
                    elif move[2].get('debit'):
                        move[2].update({
                            'debit':abs(amt),
                        })
        return move_lines
    
    
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
    
