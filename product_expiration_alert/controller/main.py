# -*- coding: utf-8 -*-
import base64
from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers.main import binary_content

class StockProductExpiration(http.Controller):

    @http.route(
        ["/web/binary/download_xls_report/<int:file>"],
        type='http',
        auth="public",
        website=True,
        sitemap=False)
    def download_proxy_detail_excel(self, file=None, **post):
        if file:
            file_id = request.env['stock.expiration.report.excel.extended'].browse([file])
            if file_id:
                status, headers, content = binary_content(model='stock.expiration.report.excel.extended', id=file_id.id, field='excel_file', filename_field=file_id.file_name, env=request.env(user=SUPERUSER_ID))
                content_base64 = base64.b64decode(content) if content else ''
                headers.append(('Content-Type', 'application/vnd.ms-excel'))
                headers.append(('Content-Disposition', 'attachment; filename=' + file_id.file_name + ';'))
                return request.make_response(content_base64, headers)
        return False
