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
    l10n_co_software_id = fields.Char(
        string="Software ID", help="Identificador del Software provisto por la DIAN"
    )
    l10n_co_software_pin = fields.Char(
        string="Software PIN", help="PIN de 5 dígitos del Software"
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

    # Campos de Resolución
    l10n_co_resolution_number = fields.Char("Número de Resolución")
    l10n_co_resolution_prefix = fields.Char("Prefijo")
    l10n_co_resolution_date_from = fields.Date("Fecha Desde")
    l10n_co_resolution_date_to = fields.Date("Fecha Hasta")
    l10n_co_resolution_range_from = fields.Integer("Rango Desde")
    l10n_co_resolution_range_to = fields.Integer("Rango Hasta")
    l10n_co_technical_key = fields.Char("Clave Técnica")
