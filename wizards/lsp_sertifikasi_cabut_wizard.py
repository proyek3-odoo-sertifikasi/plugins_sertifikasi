# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LspSertifikasiCabutWizard(models.TransientModel):
    _name = 'lsp.sertifikasi.cabut.wizard'
    _description = 'Wizard Pencabutan Sertifikat'

    sertifikasi_id = fields.Many2one(
        comodel_name='lsp.sertifikasi',
        string='Sertifikat',
        required=True,
        readonly=True,
    )
    alasan_cabut = fields.Text(
        string='Alasan Pencabutan',
        required=True,
    )

    def action_konfirmasi_cabut(self):
        self.ensure_one()
        sertifikasi = self.sertifikasi_id
        if not self.alasan_cabut:
            raise UserError(_('Alasan pencabutan wajib diisi.'))
        sertifikasi.write({
            'state': 'revoked',
            'alasan_cabut': self.alasan_cabut,
        })
        sertifikasi.message_post(
            body=_('Sertifikat <b>%s</b> telah dicabut. Alasan: %s')
            % (sertifikasi.nomor_sertifikat, self.alasan_cabut),
        )
        return {'type': 'ir.actions.act_window_close'}