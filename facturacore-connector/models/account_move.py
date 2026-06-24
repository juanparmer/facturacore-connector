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
        adquirente, desglose de impuestos, líneas de factura y resolución.
        """
        self.ensure_one()
        issue_date_str = fields.Datetime.now().strftime("%Y-%m-%dT%H:%M:%S-05:00")
        invoice_type = "01" if self.move_type == "out_invoice" else "91"

        # Agrupar impuestos a nivel de documento
        # La DIAN exige siempre el nodo TaxTotal, aunque el monto sea 0
        taxes_payload = []
        iva_tax = 0.0
        iva_pct = 0.0
        for tax_line in self.line_ids.filtered(lambda l: l.display_type == 'tax'):
            if tax_line.tax_line_id and tax_line.tax_line_id.amount > 0:
                iva_tax += abs(tax_line.balance)
                iva_pct = tax_line.tax_line_id.amount

        taxes_payload.append({
            "tax_code": "01",
            "percentage": iva_pct if iva_pct else 0.0,
            "base_amount": self.amount_untaxed,
            "tax_amount": iva_tax if iva_tax else 0.0,
            "name": "IVA"
        })

        # Construir líneas de factura
        lines_payload = []
        for index, line in enumerate(self.invoice_line_ids, start=1):
            line_taxes = []
            for tax in line.tax_ids.filtered(lambda t: t.amount_type == 'percent'):
                # Calcular el monto real del impuesto para esta línea
                tax_amount_line = line.price_subtotal * (tax.amount / 100.0)
                line_taxes.append({
                    "tax_code": "01",  # IVA
                    "percentage": tax.amount,
                    "base_amount": line.price_subtotal,
                    "tax_amount": tax_amount_line,
                    "name": tax.name or "IVA"
                })
            
            lines_payload.append({
                "local_id": str(index),
                "description": line.name or "Producto/Servicio",
                "quantity": line.quantity,
                "price_amount": line.price_unit,
                "line_extension_amount": line.price_subtotal,
                "unit_code": "94",
                "taxes": line_taxes
            })

        return {
            "invoice_header": {
                "local_id": self.name,
                "invoice_type": invoice_type,
                "issue_date": issue_date_str,
                "dian_environment": self.company_id.l10n_co_dian_environment,
                "software_id": self.company_id.l10n_co_software_id or "",
                "software_pin": self.company_id.l10n_co_software_pin or "",
                "resolution": {
                    "prefix": self.company_id.l10n_co_resolution_prefix or "SETT",
                    "number": self.company_id.l10n_co_resolution_number or "18760000001",
                    "date_from": str(self.company_id.l10n_co_resolution_date_from or "2020-01-01"),
                    "date_to": str(self.company_id.l10n_co_resolution_date_to or "2030-01-01"),
                    "range_from": self.company_id.l10n_co_resolution_range_from or 1,
                    "range_to": self.company_id.l10n_co_resolution_range_to or 5000000,
                    "technical_key": self.company_id.l10n_co_technical_key or "fc8eac422eba16e22ffd8c6f94b3f40a6e38162c"
                }
            },
            "emitter": {
                "nit": self.company_id.vat or "900123456-1",
                "company_name": self.company_id.name,
                "city_code": "11001",
                "city_name": "Bogotá",
                "department": "Bogotá",
                "department_code": "11",
                "address": self.company_id.street or "Calle 1",
                "tax_level_code": "O-99",
                "tax_scheme_id": "01",
                "tax_scheme_name": "IVA"
            },
            "buyer": {
                "identification": self.partner_id.vat or "10203040",
                "name": self.partner_id.name,
                "city_code": "11001",
                "city_name": "Bogotá",
                "department": "Bogotá",
                "department_code": "11",
                "address": self.partner_id.street or "Calle 1",
                "tax_level_code": "R-99-PN",
                "tax_scheme_id": "01",
                "tax_scheme_name": "IVA",
                "company_id_scheme_name": "31" if len(self.partner_id.vat or "") > 9 else "13"
            },
            "financials": {
                "currency": self.currency_id.name or "COP",
                "subtotal": self.amount_untaxed,
                "total_taxes": self.amount_tax,
                "total_payable": self.amount_total,
            },
            "taxes": taxes_payload,
            "lines": lines_payload,
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
