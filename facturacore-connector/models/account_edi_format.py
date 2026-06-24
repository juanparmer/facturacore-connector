# -*- coding: utf-8 -*-

import requests
import base64

from odoo import _, models


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    def _needs_web_services(self):
        """
        Indica a Odoo que este formato requiere servicios externos,
        activando el procesamiento asíncrono nativo para el conector de Colombia.
        """
        if self.code == "facturacore_co":
            return True
        return super()._needs_web_services()

    def _get_co_facturacore_api_dependencies(self):
        """
        Define las dependencias o filtros específicos para que este formato
        sea considerado en el flujo de Colombia.
        """
        return ["l10n_co_facturacore_connector"]

    def _is_compatible_with_move(self, move):
        """
        Filtra para que este formato solo aplique a facturas de Colombia.
        """
        res = super()._is_compatible_with_move(move)
        if move.country_code != "CO":
            return False
        return res

    def _is_required_for_invoice(self, move):
        """
        Retorna True si el documento es una factura saliente o nota de crédito en Colombia.
        """
        if move.country_code != "CO" or move.move_type not in (
            "out_invoice",
            "out_refund",
        ):
            return False
        return True

    def _check_invoice_configuration(self, move):
        """
        Valida que la compañía tenga configurada la API Key y la URL de FacturaCore.
        """
        errors = super()._check_invoice_configuration(move)
        if move.country_code == "CO":
            if not move.company_id.facturacore_api_key:
                errors.append(
                    _(
                        "La API Key de FacturaCore no está configurada en los ajustes de la compañía."
                    )
                )
            if (
                not hasattr(move.company_id, "facturacore_api_url")
                or not move.company_id.facturacore_api_url
            ):
                errors.append(
                    _("La URL de conexión para FacturaCore no ha sido definida.")
                )
        return errors

    def _get_move_applicability(self, move):
        """
        Mapea las funciones del framework EDI a los métodos de FacturaCore.
        """
        self.ensure_one()
        if self.code != "facturacore_co":
            return super()._get_move_applicability(move)

        return {
            "post": self._post_invoice_edi,
            "edi_content": self._get_facturacore_edi_content,
        }

    def _post_invoice_edi(self, invoices):
        """
        Método principal del framework EDI. Maneja el envío inicial a la cola
        y la verificación posterior del estado.
        """
        if self.code != "facturacore_co":
            return {}

        res = {}
        for invoice in invoices:
            edi_doc = invoice.edi_document_ids.filtered(
                lambda d: d.edi_format_id == self
            )
            api_url = invoice.company_id.facturacore_api_url

            if not api_url:
                res[invoice] = {
                    "error": _("URL de la API no configurada."),
                    "blocking_level": "error",
                }
                continue

            # PASO 1: Enviar a la cola si no tenemos task_id
            if not edi_doc.l10n_co_facturacore_task_id:
                payload = (
                    invoice._build_facturacore_json_payload()
                )  # Usamos el método de account_move.py
                try:
                    response = requests.post(
                        f"{api_url}/api/v1/invoices/process", json=payload, timeout=15
                    )
                    if response.status_code == 200:
                        task_id = response.json().get("task_id")
                        edi_doc.write({"l10n_co_facturacore_task_id": task_id})
                        invoice.write({"l10n_co_dian_status": "processing"})
                        # Dejamos la factura en estado 'to_send' para que el próximo ciclo verifique el estado
                        res[invoice] = {
                            "error": _(
                                "⏳ Documento encolado en FacturaCore (Task ID: %s). Verificando respuesta..."
                            )
                            % task_id,
                            "blocking_level": "info",
                        }
                    else:
                        res[invoice] = {
                            "error": _("Error al encolar: %s") % response.text,
                            "blocking_level": "error",
                        }
                except Exception as e:
                    res[invoice] = {
                        "error": _("Fallo de conexión al encolar: %s") % str(e),
                        "blocking_level": "warning",
                    }
                continue

            # PASO 2: Verificar estado si ya tenemos task_id
            task_id = edi_doc.l10n_co_facturacore_task_id
            try:
                status_response = requests.get(
                    f"{api_url}/api/v1/invoices/status/{task_id}", timeout=15
                )
                if status_response.status_code == 200:
                    res_data = status_response.json()
                    api_status = res_data.get("status")

                    if api_status == "SUCCESS":
                        # 1. Entramos al nivel de 'result'
                        api_result = res_data.get("result", {})

                        # 2. Entramos al nivel de 'dian_outcome' que viene de tu FastAPI
                        dian_outcome = api_result.get("dian_outcome", {})
                        dian_status = dian_outcome.get(
                            "dian_status"
                        )  # Ahora sí leerá 'CRITICAL_FAIL'

                        if dian_status == "ACEPTADO":
                            xml_string = dian_outcome.get(
                                "readable_xml"
                            )  # Correctamente obtenemos readable_xml de dian_outcome
                            attachment = self.env["ir.attachment"].create(
                                {
                                    "name": f"{invoice.name.replace('/', '_')}_DIAN.xml",  # Mantener el sufijo _DIAN
                                    "res_model": "account.move",
                                    "res_id": invoice.id,
                                    "type": "binary",
                                    "datas": base64.b64encode(
                                        xml_string.encode("utf-8")
                                    ).decode("utf-8"),
                                    "mimetype": "application/xml",
                                }
                            )
                            invoice.write({"l10n_co_dian_status": "accepted"})
                            res[invoice] = {
                                "success": True,
                                "attachment": attachment,
                            }  # Odoo vinculará este adjunto
                            if hasattr(invoice, "l10n_co_cufe"):
                                invoice.write(
                                    {"l10n_co_cufe": api_result.get("cufe")}
                                )  # CUFE está en el nivel api_result
                                if hasattr(invoice, "_generate_dian_qr"):
                                    invoice._generate_dian_qr(api_result.get("cufe"))

                        elif dian_status in (
                            "RECHAZADO",
                            "RECHAZADO_SOAP",
                            "ERROR_DESCOMPRESION_PARSEO",
                        ):
                            # Para cualquier fallo definitivo de la DIAN o errores críticos de XML
                            error_msg = (
                                dian_outcome.get("dian_description")
                                or dian_outcome.get("error_message")
                                or _("Error desconocido de la DIAN.")
                            )
                            invoice.write({"l10n_co_dian_status": "rejected"})
                            res[invoice] = {
                                "error": _("❌ Fallo DIAN (%s): %s")
                                % (dian_status, error_msg),
                                "blocking_level": "error",
                            }

                        else:
                            # Errores técnicos (CRITICAL_FAIL, ERROR_COMUNICACION, etc.)
                            # No marcamos como 'rejected' para permitir reintentos fáciles
                            res[invoice] = {
                                "error": _(
                                    "⏳ Error técnico/comunicación DIAN (%s): %s"
                                )
                                % (
                                    dian_status,
                                    dian_outcome.get("error_message")
                                    or _("Timeout de lectura o error desconocido. Reintente."),
                                ),
                                "blocking_level": "warning",
                            }

                    elif api_status == "PROCESSING":
                        res[invoice] = {
                            "error": _(
                                "⏳ El procesamiento sigue en curso en la DIAN/API."
                            ),
                            "blocking_level": "info",
                        }

                    elif api_status == "ERROR":
                        # El worker falló completamente (ej. agotó reintentos por Timeout DIAN)
                        # Limpiamos el task_id para que Odoo lo vuelva a encolar en el próximo intento
                        edi_doc.write({"l10n_co_facturacore_task_id": False})
                        invoice.write({"l10n_co_dian_status": "not_sent"})
                        res[invoice] = {
                            "error": _("Error de conexión DIAN en el Worker (Timeout agotado): %s")
                            % (res_data.get("message") or _("Revise los logs de la API")),
                            "blocking_level": "warning",
                        }
                else:
                    res[invoice] = {
                        "error": _("Error de HTTP al verificar estado: %s")
                        % status_response.status_code
                    }
            except Exception as e:
                res[invoice] = {
                    "error": _("Error conectando con verificador: %s") % str(e),
                    "blocking_level": "warning",
                }

        return res

    def _get_facturacore_edi_content(self, move):
        """
        Requerido por Odoo para pre-calcular o almacenar el contenido base si es necesario.
        """
        return b""
