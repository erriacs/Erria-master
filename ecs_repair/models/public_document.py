'''public.document'''
import os
import base64

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PublicDocument(models.Model):
    '''new model public.document'''
    _name = 'public.document'
    _description = 'Public Document'

    repair_line_id = fields.Many2one('repair.order.damage', copy=False)
    repair_order_id = fields.Many2one('repair.order',copy=False)
    document = fields.Binary("Document File", copy=False)
    document_name = fields.Char(copy=False)
    filesize = fields.Char("File", copy=False, compute="_compute_filesize")
    shareable_link = fields.Char(copy=False)
    hash_check = fields.Integer(copy=False)
    generated = fields.Boolean(default=False, copy=False)
    attachment_id = fields.Many2one('ir.attachment', copy=False)
    evidance = fields.Char(copy=False)
    

    def generate_link(self):
        ''' generate share link '''
        if not self.document:
            raise UserError("Document is empty!")
        if os.path.splitext(self.document_name)[1].upper() != ".JPG":
            raise UserError("Make sure document you upload must be in JPG format!")
        hash_check = hash(self.hash_check)
        vals = {
            'name': self.document_name,
            'datas': self.document,
            'datas_fname': self.document_name,
            'type': 'binary',
            'res_id': hash_check,
        }
        attachment_id = self.env['ir.attachment'].sudo().create(vals)
        get_url = self.env['ir.config_parameter'].search([
            ('key', '=', 'web.base.url')
        ], limit=1).value
        url = get_url + "/shareable/document/jpg/" + str(attachment_id.id) + "/" + str(hash_check)
        self.write({
            'shareable_link': url,
            'generated': True,
            'attachment_id': attachment_id.id,
        })

    @api.multi
    def write(self, vals):
        ''' extend to update attachment '''
        res = super(PublicDocument, self).write(vals)
        for public in self:
            if 'document' in vals and public.attachment_id:
                public.attachment_id.datas = vals.get('document')
            
        return res
    
    @api.multi
    def delete_document(self):
        for public in self:
            public.document = False
            public.document_name = False

    @api.multi
    def unlink(self):
        ''' extend to delete ir attachment '''
        for public in self:
            if public.attachment_id:
                public.attachment_id.unlink()
        return super(PublicDocument, self).unlink()

    @api.depends('document')
    def _compute_filesize(self):
        ''' compute size of file '''
        for public in self:
            filesize = ""
            if public.document:
                sizefile = base64.b64decode(public.document) if public.document else b''
                sizebytes = len(sizefile)
                sizemb = round((sizebytes / 1000000), 2)
                sizekb = round((sizebytes / 1000), 2)
                if sizemb >= 1:
                    filesize = str(sizemb) + " Mb"
                else:
                    filesize = str(sizekb) + " Kb"
            public.filesize = filesize

    def wizard_uploader(self):
        view_id = self.env.ref('ecs_repair.view_wizard_uploader_form')
        wizard_id = self.env['wizard.uploader'].create({'public_id': self.id})

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

    @api.multi
    @api.depends('document_name')
    def name_get(self):
        result = []
        for req in self:
            name = req.document_name
            result.append((req.id, name))
        return result

    