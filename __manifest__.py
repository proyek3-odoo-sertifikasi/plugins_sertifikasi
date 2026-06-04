# -*- coding: utf-8 -*-
{
    'name': 'LSP - Modul Sertifikasi',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Modul Sertifikasi Kompetensi untuk Lembaga Sertifikasi Profesi',
    'description': """
        Modul ini mengelola proses sertifikasi kompetensi LSP meliputi:
        - Generate sertifikat otomatis setelah asesi dinyatakan Kompeten
        - Sertifikat tersedia dalam format PDF
        - Verifikasi sertifikat via QR Code
        - Manajemen nomor sertifikat
        - Riwayat sertifikasi asesi
    """,
    'author': 'LSP Development Team',
    'website': 'https://lsp.example.com',
    'depends': [
        'base',
        'mail',
        'web',
        'plugins_manajement_asesor',
        'plugins_penilaian',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/ir_sequence_data.xml',

        # Views
        'views/lsp_sertifikasi_views.xml',
        'views/lsp_sertifikasi_menu.xml',
        'views/lsp_sertifikasi_verify_templates.xml',

        # Report
        'report/lsp_sertifikasi_report.xml',
        'report/lsp_sertifikasi_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'plugins_sertifikat/static/src/css/lsp_sertifikasi.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}