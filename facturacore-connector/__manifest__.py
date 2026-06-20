# -*- coding: utf-8 -*-

{
    "name": "FacturaCore API - Conector Ligero de Facturación Electrónica",
    "version": "18.0",
    "category": "Accounting/Localizations",
    "summary": "Módulo ligero de extracción de datos contables y conector con FacturaCore API centralizada.",
    "author": "Juan Pablo Arcos Merchán",
    "website": "https://www.unir.net",
    "depends": [
        "account_edi",
    ],
    "data": [
        "data/account_edi_format_data.xml",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
