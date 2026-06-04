# -*- coding: utf-8 -*-
import base64
import qrcode
import io
import uuid
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class LspSertifikasi(models.Model):
    _name = 'lsp.sertifikasi'
    _description = 'Sertifikasi Kompetensi LSP'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'nomor_sertifikat'
    _order = 'tanggal_terbit desc, id desc'

    nomor_sertifikat = fields.Char(
        string='Nomor Sertifikat',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )

    student_id = fields.Many2one(
        comodel_name='lsp.student',
        string='Asesi',
        required=True,
        tracking=True,
        ondelete='restrict',
    )

    asesmen_id = fields.Many2one(
        comodel_name='lsp.hasil.asesmen',
        string='Hasil Asesmen',
        required=True,
        tracking=True,
        ondelete='restrict',
        domain="[('student_id', '=', student_id), ('status_kelulusan', '=', 'lulus')]",
    )

    skema_id = fields.Many2one(
        comodel_name='lsp.skema.sertifikasi',
        string='Skema Sertifikasi',
        related='asesmen_id.skema_id',
        store=True,
        readonly=True,
    )

    asesor_id = fields.Many2one(
        comodel_name='res.users',
        string='Asesor Penilai',
        related='asesmen_id.asesor_id',
        store=True,
        readonly=True,
    )

    tanggal_terbit = fields.Date(
        string='Tanggal Terbit',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )

    masa_berlaku_tahun = fields.Integer(
        string='Masa Berlaku (Tahun)',
        default=3,
        required=True,
    )

    tanggal_kadaluarsa = fields.Date(
        string='Tanggal Kadaluarsa',
        compute='_compute_tanggal_kadaluarsa',
        store=True,
        tracking=True,
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Aktif'),
            ('expired', 'Kadaluarsa'),
            ('revoked', 'Dicabut'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )

    alasan_cabut = fields.Text(
        string='Alasan Pencabutan',
        tracking=True,
    )

    verification_token = fields.Char(
        string='Token Verifikasi',
        copy=False,
        readonly=True,
        index=True,
    )

    qr_code = fields.Binary(
        string='QR Code',
        attachment=True,
        readonly=True,
    )

    qr_code_filename = fields.Char(
        string='QR Code Filename',
        default='qr_sertifikat.png',
    )

    verification_url = fields.Char(
        string='URL Verifikasi',
        compute='_compute_verification_url',
        store=True,
    )

    catatan = fields.Html(string='Catatan')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Perusahaan',
        default=lambda self: self.env.company,
        required=True,
    )

    @api.depends('tanggal_terbit', 'masa_berlaku_tahun')
    def _compute_tanggal_kadaluarsa(self):
        for rec in self:
            if rec.tanggal_terbit and rec.masa_berlaku_tahun:
                rec.tanggal_kadaluarsa = rec.tanggal_terbit.replace(
                    year=rec.tanggal_terbit.year + rec.masa_berlaku_tahun
                )
            else:
                rec.tanggal_kadaluarsa = False

    @api.depends('nomor_sertifikat', 'verification_token')
    def _compute_verification_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', default='http://localhost:8069'
        )
        if base_url:
            base_url = base_url.rstrip('/')
            if base_url.endswith('/web'):
                base_url = base_url[:-4]
        for rec in self:
            if rec.verification_token:
                rec.verification_url = f"{base_url}/lsp/verify/{rec.verification_token}"
            elif rec.nomor_sertifikat and rec.nomor_sertifikat != _('New'):
                rec.verification_url = f"{base_url}/lsp/verify/{rec.nomor_sertifikat}"
            else:
                rec.verification_url = False

    _sql_constraints = [
        ('nomor_sertifikat_uniq', 'UNIQUE(nomor_sertifikat)', 'Nomor sertifikat harus unik!'),
        ('asesmen_sertifikat_uniq', 'UNIQUE(asesmen_id)', 'Sertifikat untuk hasil asesmen ini sudah pernah dibuat!'),
        ('verification_token_uniq', 'UNIQUE(verification_token)', 'Token verifikasi harus unik!'),
    ]

    @api.constrains('asesmen_id')
    def _check_asesmen_kompeten(self):
        for rec in self:
            if rec.asesmen_id and rec.asesmen_id.status_kelulusan != 'lulus':
                raise ValidationError(
                    _('Sertifikat hanya bisa dibuat untuk asesi dengan status Kelulusan LULUS!')
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('nomor_sertifikat', _('New')) == _('New'):
                vals['nomor_sertifikat'] = self.env['ir.sequence'].next_by_code('lsp.sertifikasi') or _('New')
            if not vals.get('verification_token'):
                vals['verification_token'] = uuid.uuid4().hex
        records = super(LspSertifikasi, self).create(vals_list)
        records._generate_qr_code()
        return records

    def write(self, vals):
        if 'verification_token' not in vals:
            missing_token = self.filtered(lambda r: not r.verification_token)
            for rec in missing_token:
                super(LspSertifikasi, rec).write({'verification_token': uuid.uuid4().hex})
        result = super(LspSertifikasi, self).write(vals)
        if any(f in vals for f in ('nomor_sertifikat', 'verification_url', 'verification_token')):
            self._generate_qr_code()
        return result

    def _generate_qr_code(self):
        for rec in self:
            if not rec.verification_url:
                continue
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=8,
                border=2,
            )
            qr.add_data(rec.verification_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            rec.qr_code = base64.b64encode(buffer.getvalue())

    def action_terbitkan(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Hanya sertifikat berstatus Draft yang bisa diterbitkan.'))
            if not rec.qr_code:
                rec._generate_qr_code()
            rec.state = 'active'

    def action_cabut(self):
        self.ensure_one()
        return {
            'name': _('Konfirmasi Pencabutan Sertifikat'),
            'type': 'ir.actions.act_window',
            'res_model': 'lsp.sertifikasi.cabut.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sertifikasi_id': self.id},
        }

    def action_set_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_print_sertifikat(self):
        return self.env.ref('plugins_sertifikat.action_report_lsp_sertifikat').report_action(self)

    @api.model
    def _generate_certificate(self, asesmen):
        existing = self.search([('asesmen_id', '=', asesmen.id)], limit=1)
        if existing:
            return existing
        certificate = self.create({
            'student_id': asesmen.student_id.id,
            'asesmen_id': asesmen.id,
            'state': 'active',
        })
        return certificate