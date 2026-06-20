# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    facturacore_api_url = fields.Char()
    facturacore_api_key = fields.Char(string="FacturaCore API Key")
    l10n_co_pfx_filename = fields.Char(
        string="Nombre del Archivo PFX", help="Ejemplo: empresa_a.pfx"
    )
    l10n_co_pfx_password = fields.Char(
        string="Contraseña PFX", help="Contraseña del certificado digital"
    )
    l10n_co_dian_environment = fields.Selection(
        [
            ("test", "Pruebas (Sandbox/Piloto)"),
            ("habilitation", "Habilitación (Set de Pruebas DIAN)"),
            ("production", "Producción"),
        ],
        string="Ambiente DIAN",
        default="test",
        help="Define el ambiente de la DIAN al que se enviarán los documentos electrónicos.",
    )
