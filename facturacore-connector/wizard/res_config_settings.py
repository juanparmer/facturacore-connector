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
    l10n_co_software_id = fields.Char(
        related="company_id.l10n_co_software_id", readonly=False
    )
    l10n_co_software_pin = fields.Char(
        related="company_id.l10n_co_software_pin", readonly=False
    )
    
    # Campos Resolución
    l10n_co_resolution_number = fields.Char(related="company_id.l10n_co_resolution_number", readonly=False)
    l10n_co_resolution_prefix = fields.Char(related="company_id.l10n_co_resolution_prefix", readonly=False)
    l10n_co_resolution_date_from = fields.Date(related="company_id.l10n_co_resolution_date_from", readonly=False)
    l10n_co_resolution_date_to = fields.Date(related="company_id.l10n_co_resolution_date_to", readonly=False)
    l10n_co_resolution_range_from = fields.Integer(related="company_id.l10n_co_resolution_range_from", readonly=False)
    l10n_co_resolution_range_to = fields.Integer(related="company_id.l10n_co_resolution_range_to", readonly=False)
    l10n_co_technical_key = fields.Char(related="company_id.l10n_co_technical_key", readonly=False)
