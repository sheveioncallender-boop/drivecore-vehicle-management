from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .vehicle import normalize_identifier


class PosOrder(models.Model):
    _inherit = "pos.order"

    drivecore_vehicle_id = fields.Many2one(
        "drivecore.vehicle", string="Vehicle", ondelete="restrict", index=True, check_company=True
    )
    drivecore_vehicle_ref = fields.Integer(
        string="POS Vehicle Reference", copy=False, index=True,
        help="Lightweight vehicle identifier used by the POS payload before the backend resolves the vehicle record.",
    )
    drivecore_vehicle_year = fields.Integer(string="Vehicle Year")
    drivecore_vehicle_make = fields.Char(string="Vehicle Make")
    drivecore_vehicle_model = fields.Char(string="Vehicle Model")
    drivecore_number_plate = fields.Char(string="Vehicle Number Plate", index=True)
    drivecore_vin = fields.Char(string="VIN")
    drivecore_odometer = fields.Float(string="Odometer Reading")
    drivecore_odometer_unit = fields.Selection([("km", "Kilometres"), ("mi", "Miles")], default="km")
    drivecore_odometer_note = fields.Text(string="Odometer Correction Reason")
    drivecore_customer_name = fields.Char(string="Customer Name")
    drivecore_customer_phone = fields.Char(string="Customer Phone")
    drivecore_customer_address = fields.Text(string="Customer Address")
    drivecore_service_visit_id = fields.Many2one("drivecore.service.visit", readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        prepared = [self._prepare_drivecore_pos_vals(dict(vals)) for vals in vals_list]
        orders = super().create(prepared)
        orders._ensure_drivecore_history()
        return orders

    def write(self, vals):
        if self.env.context.get("skip_drivecore_pos_history"):
            return super().write(vals)
        result = super().write(vals)
        if "state" in vals or any(key.startswith("drivecore_") for key in vals):
            self._ensure_drivecore_history()
        return result

    @api.model
    def _m2o_id(self, value):
        if isinstance(value, (list, tuple)):
            return value[0] if value else False
        if isinstance(value, dict):
            return value.get("id")
        return value or False

    @api.model
    def _prepare_drivecore_pos_vals(self, vals):
        session_id = self._m2o_id(vals.get("session_id"))
        session = self.env["pos.session"].browse(session_id).exists() if session_id else self.env["pos.session"]
        company = session.company_id if session else self.env.company

        partner_id = self._m2o_id(vals.get("partner_id"))
        partner = self.env["res.partner"].browse(partner_id).exists() if partner_id else self.env["res.partner"]
        customer_name = (vals.get("drivecore_customer_name") or "").strip()
        phone = (vals.get("drivecore_customer_phone") or "").strip()
        address = (vals.get("drivecore_customer_address") or "").strip()

        if not partner and customer_name:
            partner = self.env["res.partner"].create({
                "name": customer_name,
                "phone": phone,
                "street": address,
                "customer_rank": 1,
            })
            vals["partner_id"] = partner.id
        elif partner:
            updates = {}
            if phone and not partner.phone:
                updates["phone"] = phone
            if address and not (partner.street or partner.street2):
                updates["street"] = address
            if updates:
                partner.write(updates)

        if partner:
            if not vals.get("drivecore_customer_name"):
                vals["drivecore_customer_name"] = partner.name
            if not vals.get("drivecore_customer_phone"):
                vals["drivecore_customer_phone"] = partner.phone or ""
            if not vals.get("drivecore_customer_address"):
                vals["drivecore_customer_address"] = partner.contact_address or address

        vehicle_id = self._m2o_id(
            vals.get("drivecore_vehicle_ref") or vals.get("drivecore_vehicle_id")
        )
        vehicle = self.env["drivecore.vehicle"].browse(vehicle_id).exists() if vehicle_id else self.env["drivecore.vehicle"]
        plate = (vals.get("drivecore_number_plate") or "").strip().upper()
        vin = (vals.get("drivecore_vin") or "").strip().upper()

        if not vehicle and (plate or vin):
            identifiers = []
            if plate:
                identifiers.append(("plate_normalized", "=", normalize_identifier(plate)))
            if vin:
                identifiers.append(("vin_normalized", "=", normalize_identifier(vin)))
            identifier_domain = ["|", *identifiers] if len(identifiers) == 2 else identifiers
            vehicle = self.env["drivecore.vehicle"].search([
                ("company_id", "=", company.id),
                *identifier_domain,
            ], limit=1)

        required_vehicle_data = (
            partner
            and plate
            and vals.get("drivecore_vehicle_year")
            and vals.get("drivecore_vehicle_make")
            and vals.get("drivecore_vehicle_model")
        )
        if not vehicle and required_vehicle_data:
            make_name = vals["drivecore_vehicle_make"].strip()
            model_name = vals["drivecore_vehicle_model"].strip()
            make = self.env["drivecore.vehicle.make"].search([("name", "=ilike", make_name)], limit=1)
            if not make:
                make = self.env["drivecore.vehicle.make"].create({"name": make_name.title()})
            model = self.env["drivecore.vehicle.model"].search([
                ("make_id", "=", make.id),
                ("name", "=ilike", model_name),
            ], limit=1)
            if not model:
                model = self.env["drivecore.vehicle.model"].create({
                    "make_id": make.id,
                    "name": model_name.title(),
                })
            vehicle = self.env["drivecore.vehicle"].create({
                "partner_id": partner.id,
                "company_id": company.id,
                "year": int(vals["drivecore_vehicle_year"]),
                "make_id": make.id,
                "model_id": model.id,
                "license_plate": plate,
                "vin": vin,
                "odometer_unit": vals.get("drivecore_odometer_unit") or "km",
            })

        if vehicle:
            vals["drivecore_vehicle_id"] = vehicle.id
            vals["drivecore_vehicle_ref"] = vehicle.id
            vals["partner_id"] = vehicle.partner_id.id
            if not vals.get("drivecore_vehicle_year"):
                vals["drivecore_vehicle_year"] = vehicle.year
            if not vals.get("drivecore_vehicle_make"):
                vals["drivecore_vehicle_make"] = vehicle.make_id.name
            if not vals.get("drivecore_vehicle_model"):
                vals["drivecore_vehicle_model"] = vehicle.model_id.name
            if not vals.get("drivecore_number_plate"):
                vals["drivecore_number_plate"] = vehicle.license_plate
            if not vals.get("drivecore_vin"):
                vals["drivecore_vin"] = vehicle.vin
            if not vals.get("drivecore_odometer_unit"):
                vals["drivecore_odometer_unit"] = vehicle.odometer_unit
            if not vals.get("drivecore_customer_name"):
                vals["drivecore_customer_name"] = vehicle.partner_id.name
            if not vals.get("drivecore_customer_phone"):
                vals["drivecore_customer_phone"] = vehicle.partner_id.phone or ""
            if not vals.get("drivecore_customer_address"):
                vals["drivecore_customer_address"] = vehicle.partner_id.contact_address or ""

        return vals

    def _drivecore_requires_vehicle_details(self):
        self.ensure_one()
        if self.is_refund or self.refunded_order_id:
            return False
        policy = self.config_id.drivecore_vehicle_policy or "optional"
        if policy == "optional":
            return False
        if policy == "all":
            return True
        return any(self.lines.mapped("product_id.drivecore_requires_vehicle"))

    def _validate_drivecore_checkout_details(self):
        for order in self:
            if not order._drivecore_requires_vehicle_details():
                continue
            config = order.config_id
            missing = []
            if not order.drivecore_vehicle_id:
                missing.append(_("Vehicle profile"))
            if config.drivecore_require_customer_name and not (order.drivecore_customer_name or "").strip():
                missing.append(_("Customer name"))
            if config.drivecore_require_phone and not (order.drivecore_customer_phone or "").strip():
                missing.append(_("Phone number"))
            if config.drivecore_require_address and not (order.drivecore_customer_address or "").strip():
                missing.append(_("Address"))
            if config.drivecore_require_year and not order.drivecore_vehicle_year:
                missing.append(_("Vehicle year"))
            if config.drivecore_require_make_model and not (order.drivecore_vehicle_make or "").strip():
                missing.append(_("Vehicle make"))
            if config.drivecore_require_make_model and not (order.drivecore_vehicle_model or "").strip():
                missing.append(_("Vehicle model"))
            if config.drivecore_require_plate and not (order.drivecore_number_plate or "").strip():
                missing.append(_("Number plate"))
            if config.drivecore_require_vin and not (order.drivecore_vin or "").strip():
                missing.append(_("VIN"))
            if config.drivecore_require_odometer and order.drivecore_odometer < 0:
                missing.append(_("Valid odometer reading"))
            if missing:
                raise ValidationError(
                    _("Complete the required DriveCore checkout details: %(fields)s", fields=", ".join(missing))
                )

    def _ensure_drivecore_history(self):
        completed_states = ("paid", "done", "invoiced")
        for order in self.filtered(lambda record: record.drivecore_vehicle_id and record.state in completed_states):
            if getattr(order, "is_refund", False) or order.refunded_order_id:
                continue

            odometer = self.env["drivecore.vehicle.odometer"].search([
                ("pos_order_id", "=", order.id),
            ], limit=1)
            odometer_vals = {
                "vehicle_id": order.drivecore_vehicle_id.id,
                "reading": order.drivecore_odometer,
                "reading_date": order.date_order,
                "source": "pos",
                "pos_order_id": order.id,
            }
            if order.drivecore_odometer_note:
                odometer_vals["lower_reading_reason"] = order.drivecore_odometer_note
            elif odometer and odometer.lower_reading_reason:
                odometer_vals["lower_reading_reason"] = odometer.lower_reading_reason
            if odometer:
                odometer.write(odometer_vals)
            else:
                self.env["drivecore.vehicle.odometer"].create(odometer_vals)

            if not order.drivecore_service_visit_id:
                service_types = order.lines.mapped("product_id.drivecore_service_type_id")
                visit = self.env["drivecore.service.visit"].create({
                    "partner_id": order.partner_id.id,
                    "vehicle_id": order.drivecore_vehicle_id.id,
                    "company_id": order.company_id.id,
                    "visit_date": order.date_order,
                    "state": "done",
                    "service_type_ids": [(6, 0, service_types.ids)],
                    "odometer": order.drivecore_odometer,
                    "odometer_note": order.drivecore_odometer_note,
                    "pos_order_id": order.id,
                    "work_performed": "\n".join(filter(None, order.lines.mapped("full_product_name"))),
                })
                order.with_context(skip_drivecore_pos_history=True).write({
                    "drivecore_service_visit_id": visit.id,
                })

    def _process_saved_order(self, draft):
        if not draft:
            self._validate_drivecore_checkout_details()
        result = super()._process_saved_order(draft)
        self._ensure_drivecore_history()
        return result

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        if len(self) == 1:
            order = self
            vals.update({
                "drivecore_vehicle_id": order.drivecore_vehicle_id.id,
                "drivecore_vehicle_year": order.drivecore_vehicle_year,
                "drivecore_vehicle_make": order.drivecore_vehicle_make,
                "drivecore_vehicle_model": order.drivecore_vehicle_model,
                "drivecore_number_plate": order.drivecore_number_plate,
                "drivecore_vin": order.drivecore_vin,
                "drivecore_odometer": order.drivecore_odometer,
                "drivecore_odometer_unit": order.drivecore_odometer_unit,
                "drivecore_odometer_note": order.drivecore_odometer_note,
                "drivecore_service_visit_id": order.drivecore_service_visit_id.id,
            })
        return vals
