# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request


class LspSertifikasiVerifyController(http.Controller):
    @http.route(
        ['/lsp/verify/<string:token>'],
        type='http',
        auth='public',
        website=False,
        sitemap=False,
        methods=['GET'],
    )
    def verify_certificate(self, token, **kwargs):
        Sertifikasi = request.env['lsp.sertifikasi'].sudo()

        certificate = Sertifikasi.search([('verification_token', '=', token)], limit=1)
        # Backward compatibility: older QR/link might use nomor_sertifikat
        if not certificate:
            certificate = Sertifikasi.search([('nomor_sertifikat', '=', token)], limit=1)

        if not certificate:
            response = request.render(
                'plugins_sertifikasi.verify_not_found',
                {'token': token},
            )
            response.headers['Cache-Control'] = 'no-store'
            return response

        today = fields.Date.today()
        expired_by_date = bool(
            certificate.tanggal_kadaluarsa and certificate.tanggal_kadaluarsa < today
        )
        is_valid = certificate.state == 'active' and not expired_by_date

        response = request.render(
            'plugins_sertifikasi.verify_page',
            {
                'cert': certificate,
                'is_valid': is_valid,
                'expired_by_date': expired_by_date,
                'today': today,
            },
        )
        response.headers['Cache-Control'] = 'no-store'
        return response
