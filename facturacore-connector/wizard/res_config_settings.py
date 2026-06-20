# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    facturacore_api_url = fields.Char(
        related="company_id.facturacore_api_url", readonly=False
    )
    facturacore_api_key = fields.Char(
        related="company_id.facturacore_api_key", readonly=False
    )
    l10n_co_pfx_filename = fields.Char(
        related="company_id.l10n_co_pfx_filename", readonly=False
    )
    l10n_co_pfx_password = fields.Char(
        related="company_id.l10n_co_pfx_password", readonly=False
    )
    l10n_co_dian_environment = fields.Selection(
        related="company_id.l10n_co_dian_environment",
        string="Ambiente DIAN",
        readonly=False,
    )
