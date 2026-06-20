# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_co_dian_status = fields.Selection(
        [
            ("not_sent", "No Enviado"),
            ("processing", "Procesando en Cola"),
            ("accepted", "Aceptado por la DIAN"),
            ("rejected", "Rechazado por la DIAN"),
        ],
        string="Estado DIAN",
        default="not_sent",
        copy=False,
        readonly=True,
    )

    l10n_co_cufe = fields.Char(string="CUFE", copy=False, readonly=True)

    def _build_facturacore_json_payload(self):
        """
        Genera el diccionario con los datos robustos del asiento contable
        exigidos por Pydantic en FacturaCore API, incluyendo cabeceras, emisor,
        adquirente y desglose de impuestos.
        """
        self.ensure_one()
        issue_date_str = fields.Datetime.now().strftime("%Y-%m-%dT%H:%M:%S-05:00")
        invoice_type = "01" if self.move_type == "out_invoice" else "91"

        taxes_payload = []
        if self.amount_tax > 0:
            taxes_payload.append(
                {
                    "tax_code": "01",
                    "percentage": 19.0,
                    "base_amount": self.amount_untaxed,
                    "tax_amount": self.amount_tax,
                }
            )
        else:
            taxes_payload.append(
                {
                    "tax_code": "01",
                    "percentage": 0.0,
                    "base_amount": self.amount_untaxed,
                    "tax_amount": 0.0,
                }
            )

        return {
            "invoice_header": {
                "local_id": self.name,
                "invoice_type": invoice_type,
                "issue_date": issue_date_str,
                "dian_environment": self.company_id.l10n_co_dian_environment,
            },
            "emitter": {
                "nit": self.company_id.vat or "900123456-1",
                "company_name": self.company_id.name,
            },
            "buyer": {
                "identification": self.partner_id.vat
                or "10203040",
                "name": self.partner_id.name,
            },
            "financials": {
                "currency": self.currency_id.name
                or "COP",
                "subtotal": self.amount_untaxed,
                "total_taxes": self.amount_tax,
                "total_payable": self.amount_total,
            },
            "taxes": taxes_payload,
            "certificate_config": {
                "pfx_name": str(self.company_id.l10n_co_pfx_filename or "DEMO_CERT"),
                "pfx_password": str(
                    self.company_id.l10n_co_pfx_password or "DEMO_PASSWORD"
                ),
            },
        }

    def button_check_dian_status_manual(self):
        """
        Acción manual que permite al usuario verificar el estado actual de
        un documento que está en estado 'Procesando' sin esperar al Cron.
        """
        self.ensure_one()
        edi_format = self.env.ref("facturacore_connector.edi_facturacore_co")
        edi_doc = self.edi_document_ids.filtered(
            lambda d: d.edi_format_id == edi_format
        )
        if not edi_doc:
            raise UserError(_("No hay un documento EDI de FacturaCore asociado."))
        edi_format._post_invoice_edi(self)
        return True
