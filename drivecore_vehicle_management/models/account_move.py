from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    drivecore_vehicle_id = fields.Many2one(
        "drivecore.vehicle", string="Vehicle", ondelete="restrict", index=True, check_company=True
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
        if self.env.context.get("skip_drivecore_invoice_history"):
            return super().write(vals)
        if "drivecore_vehicle_id" in vals:
            vehicle = self.env["drivecore.vehicle"].browse(vals.get("drivecore_vehicle_id")).exists()
            vals = {**vals, **self._drivecore_snapshot_vals(vehicle)}
        return super().write(vals)

    @api.constrains("drivecore_vehicle_id", "partner_id", "company_id")
    def _check_drivecore_vehicle_customer_company(self):
        for move in self:
            if not move.drivecore_vehicle_id:
                continue
            if move.partner_id and move.partner_id.commercial_partner_id != move.drivecore_vehicle_id.partner_id.commercial_partner_id:
                raise ValidationError(_("The invoice customer must match the selected vehicle owner."))
            if move.company_id != move.drivecore_vehicle_id.company_id:
                raise ValidationError(_("The invoice and selected vehicle must belong to the same company."))

    @api.onchange("drivecore_vehicle_id")
    def _onchange_drivecore_vehicle_id(self):
        for move in self:
            if move.drivecore_vehicle_id:
                move.update(self._drivecore_snapshot_vals(move.drivecore_vehicle_id))

    def action_post(self):
        result = super().action_post()
        for move in self.filtered(
            lambda record: record.drivecore_vehicle_id and record.move_type in ("out_invoice", "out_receipt")
        ):
            move._ensure_drivecore_history()
        return result

    def _ensure_drivecore_history(self):
        self.ensure_one()
        Odometer = self.env["drivecore.vehicle.odometer"]
        ServiceVisit = self.env["drivecore.service.visit"]

        linked_visit = self.drivecore_service_visit_id
        if not linked_visit:
            sale_orders = self.invoice_line_ids.sale_line_ids.order_id.filtered(
                lambda order: order.drivecore_vehicle_id == self.drivecore_vehicle_id
            )
            linked_visit = sale_orders.mapped("drivecore_service_visit_id")[:1]
        if not linked_visit:
            pos_order = self.env["pos.order"].search([
                ("account_move", "=", self.id),
                ("drivecore_vehicle_id", "=", self.drivecore_vehicle_id.id),
            ], limit=1)
            linked_visit = pos_order.drivecore_service_visit_id

        existing_odometer = Odometer.search([("invoice_id", "=", self.id)], limit=1)
        if not existing_odometer and linked_visit and linked_visit.odometer_record_id:
            existing_odometer = linked_visit.odometer_record_id

        odometer_vals = {
            "vehicle_id": self.drivecore_vehicle_id.id,
            "reading": self.drivecore_odometer,
            "reading_date": (
                fields.Datetime.to_datetime(self.invoice_date)
                if self.invoice_date
                else fields.Datetime.now()
            ),
            "invoice_id": self.id,
        }
        if existing_odometer:
            if self.drivecore_odometer_note:
                odometer_vals["lower_reading_reason"] = self.drivecore_odometer_note
            existing_odometer.write(odometer_vals)
        else:
            odometer_vals["source"] = "invoice"
            if self.drivecore_odometer_note:
                odometer_vals["lower_reading_reason"] = self.drivecore_odometer_note
            existing_odometer = Odometer.create(odometer_vals)

        if linked_visit:
            visit_vals = {"invoice_id": self.id}
            if not linked_visit.odometer_record_id:
                visit_vals["odometer_record_id"] = existing_odometer.id
            linked_visit.with_context(skip_drivecore_visit_history=True).write(visit_vals)
            if self.drivecore_service_visit_id != linked_visit:
                self.with_context(skip_drivecore_invoice_history=True).write({
                    "drivecore_service_visit_id": linked_visit.id,
                })
            return

        service_types = self.invoice_line_ids.product_id.mapped("drivecore_service_type_id")
        visit = ServiceVisit.create({
            "partner_id": self.partner_id.id,
            "vehicle_id": self.drivecore_vehicle_id.id,
            "company_id": self.company_id.id,
            "visit_date": fields.Datetime.now(),
            "state": "done",
            "service_type_ids": [(6, 0, service_types.ids)],
            "odometer": self.drivecore_odometer,
            "odometer_note": self.drivecore_odometer_note,
            "customer_request": self.drivecore_customer_request,
            "technician_findings": self.drivecore_technician_findings,
            "invoice_id": self.id,
            "odometer_record_id": existing_odometer.id,
            "work_performed": "\n".join(filter(None, self.invoice_line_ids.mapped("name"))),
        })
        self.with_context(skip_drivecore_invoice_history=True).write({
            "drivecore_service_visit_id": visit.id,
        })
