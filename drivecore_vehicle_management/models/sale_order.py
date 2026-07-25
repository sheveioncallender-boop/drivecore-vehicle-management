from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    drivecore_vehicle_id = fields.Many2one(
        "drivecore.vehicle", string="Vehicle", ondelete="restrict", index=True, tracking=True, check_company=True
    )
    drivecore_vehicle_year = fields.Integer(string="Vehicle Year")
    drivecore_vehicle_make = fields.Char(string="Vehicle Make")
    drivecore_vehicle_model = fields.Char(string="Vehicle Model")
    drivecore_number_plate = fields.Char(string="Vehicle Number Plate", index=True)
    drivecore_vin = fields.Char(string="VIN")
    drivecore_odometer = fields.Float(string="Odometer Reading")
    drivecore_odometer_unit = fields.Selection([("km", "Kilometres"), ("mi", "Miles")], default="km")
    drivecore_odometer_note = fields.Text(string="Odometer Correction Reason")
    drivecore_service_type_id = fields.Many2one("drivecore.service.type", string="Primary Service")
    drivecore_customer_request = fields.Text(string="Customer Request / Complaint")
    drivecore_technician_findings = fields.Text(string="Technician Findings")
    drivecore_service_visit_id = fields.Many2one("drivecore.service.visit", readonly=True, copy=False)

    @api.model
    def _drivecore_snapshot_vals(self, vehicle):
        if not vehicle:
            return {
                "drivecore_vehicle_year": 0,
                "drivecore_vehicle_make": False,
                "drivecore_vehicle_model": False,
                "drivecore_number_plate": False,
                "drivecore_vin": False,
                "drivecore_odometer": 0.0,
                "drivecore_odometer_unit": "km",
            }
        return {
            "partner_id": vehicle.partner_id.id,
            "drivecore_vehicle_year": vehicle.year,
            "drivecore_vehicle_make": vehicle.make_id.name,
            "drivecore_vehicle_model": vehicle.model_id.name,
            "drivecore_number_plate": vehicle.license_plate,
            "drivecore_vin": vehicle.vin,
            "drivecore_odometer": vehicle.current_odometer,
            "drivecore_odometer_unit": vehicle.odometer_unit,
        }

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for values in vals_list:
            vals = dict(values)
            vehicle = self.env["drivecore.vehicle"].browse(vals.get("drivecore_vehicle_id")).exists()
            if vehicle:
                snapshot = self._drivecore_snapshot_vals(vehicle)
                for key, value in snapshot.items():
                    vals.setdefault(key, value)
            prepared.append(vals)
        return super().create(prepared)

    def write(self, vals):
        if "drivecore_vehicle_id" in vals:
            vehicle = self.env["drivecore.vehicle"].browse(vals.get("drivecore_vehicle_id")).exists()
            vals = {**vals, **self._drivecore_snapshot_vals(vehicle)}
        return super().write(vals)

    @api.constrains("drivecore_vehicle_id", "partner_id", "company_id")
    def _check_drivecore_vehicle_customer_company(self):
        for order in self:
            if not order.drivecore_vehicle_id:
                continue
            if order.partner_id and order.partner_id.commercial_partner_id != order.drivecore_vehicle_id.partner_id.commercial_partner_id:
                raise ValidationError(_("The quotation customer must match the selected vehicle owner."))
            if order.company_id != order.drivecore_vehicle_id.company_id:
                raise ValidationError(_("The quotation and selected vehicle must belong to the same company."))

    @api.onchange("drivecore_vehicle_id")
    def _onchange_drivecore_vehicle_id(self):
        self._set_drivecore_vehicle_snapshot()

    def _set_drivecore_vehicle_snapshot(self):
        for order in self:
            vehicle = order.drivecore_vehicle_id
            if vehicle:
                order.update(self._drivecore_snapshot_vals(vehicle))

    def action_confirm(self):
        result = super().action_confirm()
        for order in self.filtered("drivecore_vehicle_id"):
            order._ensure_drivecore_history()
        return result

    def _ensure_drivecore_history(self):
        self.ensure_one()
        if not self.drivecore_vehicle_id:
            return

        existing = self.env["drivecore.vehicle.odometer"].search([
            ("sale_order_id", "=", self.id),
        ], limit=1)
        odometer_vals = {
            "vehicle_id": self.drivecore_vehicle_id.id,
            "reading": self.drivecore_odometer,
            "source": "sale",
            "sale_order_id": self.id,
        }
        if self.drivecore_odometer_note:
            odometer_vals["lower_reading_reason"] = self.drivecore_odometer_note
        elif existing and existing.lower_reading_reason:
            odometer_vals["lower_reading_reason"] = existing.lower_reading_reason
        if existing:
            existing.write(odometer_vals)
        else:
            self.env["drivecore.vehicle.odometer"].create(odometer_vals)

        if not self.drivecore_service_visit_id:
            service_types = self.order_line.mapped("product_id.drivecore_service_type_id")
            primary_service = self.drivecore_service_type_id or service_types[:1]
            visit = self.env["drivecore.service.visit"].create({
                "partner_id": self.partner_id.id,
                "vehicle_id": self.drivecore_vehicle_id.id,
                "company_id": self.company_id.id,
                "visit_date": self.date_order,
                "state": "draft",
                "service_type_ids": [(6, 0, service_types.ids)],
                "odometer": self.drivecore_odometer,
                "odometer_note": self.drivecore_odometer_note,
                "customer_request": self.drivecore_customer_request,
                "technician_findings": self.drivecore_technician_findings,
                "sale_order_id": self.id,
                "work_performed": primary_service.name if primary_service else False,
            })
            super(SaleOrder, self).write({"drivecore_service_visit_id": visit.id})

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update({
            "drivecore_vehicle_id": self.drivecore_vehicle_id.id,
            "drivecore_vehicle_year": self.drivecore_vehicle_year,
            "drivecore_vehicle_make": self.drivecore_vehicle_make,
            "drivecore_vehicle_model": self.drivecore_vehicle_model,
            "drivecore_number_plate": self.drivecore_number_plate,
            "drivecore_vin": self.drivecore_vin,
            "drivecore_odometer": self.drivecore_odometer,
            "drivecore_odometer_unit": self.drivecore_odometer_unit,
            "drivecore_odometer_note": self.drivecore_odometer_note,
            "drivecore_service_type_id": self.drivecore_service_type_id.id,
            "drivecore_customer_request": self.drivecore_customer_request,
            "drivecore_technician_findings": self.drivecore_technician_findings,
            "drivecore_service_visit_id": self.drivecore_service_visit_id.id,
        })
        return vals
