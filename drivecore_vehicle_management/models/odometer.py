from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DriveCoreVehicleOdometer(models.Model):
    _name = "drivecore.vehicle.odometer"
    _description = "Vehicle Odometer Reading"
    _order = "reading_date desc, id desc"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    vehicle_id = fields.Many2one("drivecore.vehicle", required=True, ondelete="cascade", index=True, tracking=True)
    company_id = fields.Many2one(related="vehicle_id.company_id", store=True, index=True)
    partner_id = fields.Many2one(related="vehicle_id.partner_id", store=True, index=True)
    reading = fields.Float(required=True, tracking=True)
    unit = fields.Selection(related="vehicle_id.odometer_unit", store=True, readonly=True)
    reading_date = fields.Datetime(default=fields.Datetime.now, required=True, index=True, tracking=True)
    source = fields.Selection([
        ("manual", "Manual Entry"),
        ("pos", "Point of Sale"),
        ("sale", "Sales Order"),
        ("invoice", "Invoice"),
        ("service", "Service Visit"),
    ], default="manual", required=True, index=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, required=True)
    notes = fields.Text()
    lower_reading_reason = fields.Text(string="Lower Reading / Correction Reason")
    pos_order_id = fields.Many2one("pos.order", ondelete="set null", index=True)
    sale_order_id = fields.Many2one("sale.order", ondelete="set null", index=True)
    invoice_id = fields.Many2one("account.move", ondelete="set null", index=True)
    service_visit_id = fields.Many2one("drivecore.service.visit", ondelete="set null", index=True)

    @api.model
    def _validate_reading_values(self, vals, record=None):
        vehicle_id = vals.get("vehicle_id") or (record.vehicle_id.id if record else False)
        if not vehicle_id:
            return
        reading = vals.get("reading", record.reading if record else 0.0)
        reading = float(reading or 0.0)
        if reading < 0:
            raise ValidationError(_("Odometer readings cannot be negative."))

        domain = [("vehicle_id", "=", vehicle_id)]
        if record:
            domain.append(("id", "!=", record.id))
        latest = self.search(domain, order="reading_date desc, id desc", limit=1)
        reason = vals.get(
            "lower_reading_reason",
            record.lower_reading_reason if record else False,
        )
        if latest and reading < latest.reading and not reason:
            raise ValidationError(_(
                "The new reading (%(new)s) is lower than the latest saved reading (%(old)s). "
                "Enter a correction reason.",
                new=reading,
                old=latest.reading,
            ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._validate_reading_values(vals)
        records = super().create(vals_list)
        records._update_vehicle_current_reading()
        return records

    def write(self, vals):
        if {"vehicle_id", "reading", "reading_date", "lower_reading_reason"} & set(vals):
            for record in self:
                self._validate_reading_values(vals, record=record)
        vehicles = self.mapped("vehicle_id")
        result = super().write(vals)
        (vehicles | self.mapped("vehicle_id"))._recompute_current_odometer_from_history()
        return result

    def unlink(self):
        vehicles = self.mapped("vehicle_id")
        result = super().unlink()
        vehicles._recompute_current_odometer_from_history()
        return result

    def _update_vehicle_current_reading(self):
        self.mapped("vehicle_id")._recompute_current_odometer_from_history()


class DriveCoreVehicleOdometerHelper(models.Model):
    _inherit = "drivecore.vehicle"

    def _recompute_current_odometer_from_history(self):
        Odometer = self.env["drivecore.vehicle.odometer"]
        for vehicle in self:
            latest = Odometer.search(
                [("vehicle_id", "=", vehicle.id)], order="reading_date desc, id desc", limit=1
            )
            vehicle.with_context(skip_odometer_history=True).write({
                "current_odometer": latest.reading if latest else 0.0,
                "current_odometer_date": latest.reading_date if latest else False,
            })
