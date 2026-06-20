# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountEdiDocument(models.Model):
    _inherit = "account.edi.document"

    # Almacena el ID de la tarea asíncrona devuelto por FastAPI/Celery
    l10n_co_facturacore_task_id = fields.Char(
        string="FacturaCore Task ID",
        copy=False,
        help="ID de la tarea en la cola de procesamiento de la API.",
    )
