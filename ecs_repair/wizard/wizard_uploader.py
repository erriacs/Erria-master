'''wizard.uploader'''
import os
import base64
from io import BytesIO
import logging
import zipfile
from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import image_resize_image, ustr


class WizardUploader(models.TransientModel):
    '''new transient model wizard.uploader'''
    _name = 'wizard.uploader'
    _description = 'Wizard Uploader'

    public_id = fields.Many2one('public.document')
    repair_line_id = fields.Many2one('repair.order.damage', copy=False)
    repair_order_id = fields.Many2one('repair.order', copy=False)
    document_fname = fields.Char()
    document = fields.Binary()
    # line_ids = fields.One2many('wizard.uploader.line', 'wizard_id')

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

    def resize_image(self, image):
        image = ustr(image).encode('utf-8')
        document = image_resize_image(image, size=(448, 336))
        return document

    def action_upload_document(self):
        ''' create/write attachment file to object public document '''
        # update image
        document = self.document
        if self.document:
            document = self.resize_image(self.document)
        if self.public_id:
            if os.path.splitext(self.document_fname)[1].upper() != ".JPG":
                raise UserError("Make sure document you upload must be in JPG format!")

            self.public_id.write({
                'document': document,
                'document_name': self.document_fname,
            })

        if self.repair_line_id:
            records = []
            #evidence 1
            if self.evidence_1:
                evd_1 = self.evidence_1
                if os.path.splitext(self.evidence_1_file)[1].upper() != ".JPG":
                    raise UserError("Make sure document you upload must be in JPG format in evidence 1!")
                evd_1 = self.resize_image(self.evidence_1)
                vals1 = {
                    'repair_line_id': self.repair_line_id.id,
                    'repair_order_id': self.repair_line_id and self.repair_line_id.repair_order_id.id,
                    'document': evd_1,
                    'document_name': self.evidence_1_file
                }
                records.append(vals1)

            #evidence 2
            if self.evidence_2:
                evd_2 = self.evidence_2
                if os.path.splitext(self.evidence_2_file)[1].upper() != ".JPG":
                    raise UserError("Make sure document you upload must be in JPG format in evidence 2!")
                evd_2 = self.resize_image(self.evidence_2)
                vals2 = {
                    'repair_line_id': self.repair_line_id.id,
                    'repair_order_id': self.repair_line_id and self.repair_line_id.repair_order_id.id,
                    'document': evd_2,
                    'document_name': self.evidence_2_file
                }
                records.append(vals2)

            #evidence 3
            if self.evidence_3:
                evd_3 = self.evidence_3
                if os.path.splitext(self.evidence_3_file)[1].upper() != ".JPG":
                    raise UserError("Make sure document you upload must be in JPG format in evidence 3!")
                evd_3 = self.resize_image(self.evidence_3)
                vals3 = {
                    'repair_line_id': self.repair_line_id.id,
                    'repair_order_id': self.repair_line_id and self.repair_line_id.repair_order_id.id,
                    'document': evd_3,
                    'document_name': self.evidence_3_file
                }
                records.append(vals3)

            #evidence 4
            if self.evidence_4:
                evd_4 = self.evidence_4
                if os.path.splitext(self.evidence_4_file)[1].upper() != ".JPG":
                    raise UserError("Make sure document you upload must be in JPG format in evidence 4!")
                evd_4 = self.resize_image(self.evidence_4)
                vals4 = {
                    'repair_line_id': self.repair_line_id.id,
                    'repair_order_id': self.repair_line_id and self.repair_line_id.repair_order_id.id,
                    'document': evd_4,
                    'document_name': self.evidence_4_file
                }
                records.append(vals4)

            #evidence 5
            if self.evidence_5:
                evd_5 = self.evidence_5
                if os.path.splitext(self.evidence_5_file)[1].upper() != ".JPG":
                    raise UserError("Make sure document you upload must be in JPG format in evidence 5!")
                evd_5 = self.resize_image(self.evidence_5)
                vals5 = {
                    'repair_line_id': self.repair_line_id.id,
                    'repair_order_id': self.repair_line_id and self.repair_line_id.repair_order_id.id,
                    'document': evd_5,
                    'document_name': self.evidence_5_file
                }
                records.append(vals5)
            
            if records:
                public_ids_len = len(self.repair_line_id.public_ids) + len(records)
                if public_ids_len > 5:
                    cek_index_record = len(range(0,5)) - len(self.repair_line_id.public_ids)
                    records = records[0:cek_index_record]
                public_document_ids = self.env['public.document'].create(records)
                # for doc in public_document_ids:
                #     doc.generate_link()
        
        if self.public_id.repair_line_id and self.public_id.repair_line_id.repair_order_id:
            self.public_id.repair_line_id.repair_order_id.action_generate_image_sequence()
        if self.repair_line_id and self.repair_line_id.repair_order_id:
            self.repair_line_id.repair_order_id.action_generate_image_sequence()


class WizardUploaderLine(models.TransientModel):
    '''new transient model wizard.uploader.line'''
    _name = 'wizard.uploader.line'
    _description = 'Wizard Uploader Line'

    wizard_id = fields.Many2one('wizard.uploader')
    document = fields.Binary()
    document_fname = fields.Char("Document Name")

