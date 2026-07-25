import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


def normalize_identifier(value):
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


class DriveCoreVehicle(models.Model):
    _name = "drivecore.vehicle"
    _description = "Customer Vehicle"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "license_plate, year desc"
    _rec_name = "name"
    _check_company_auto = True

    name = fields.Char(compute="_compute_name", store=True, index=True)
    partner_id = fields.Many2one(
        "res.partner", string="Owner", required=True, ondelete="restrict", index=True, tracking=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    active = fields.Boolean(default=True)
    year = fields.Integer(required=True, tracking=True)
    make_id = fields.Many2one("drivecore.vehicle.make", required=True, tracking=True, index=True)
    model_id = fields.Many2one(
        "drivecore.vehicle.model",
        required=True,
        tracking=True,
        index=True,
        domain="[('make_id', '=', make_id)]",
    )
    license_plate = fields.Char(string="Number Plate", required=True, tracking=True, index=True)
    plate_normalized = fields.Char(compute="_compute_identifiers", store=True, index=True)
    vin = fields.Char(string="VIN", tracking=True, index=True)
    vin_normalized = fields.Char(compute="_compute_identifiers", store=True, index=True)
    color = fields.Char()
    registration_notes = fields.Text()
    notes = fields.Html()
    odometer_unit = fields.Selection(
        [("km", "Kilometres"), ("mi", "Miles")], default="km", required=True, tracking=True
    )
    current_odometer = fields.Float(readonly=True, tracking=True)
    current_odometer_date = fields.Datetime(readonly=True)

    owner_name = fields.Char(compute="_compute_owner_snapshot")
    owner_phone = fields.Char(compute="_compute_owner_snapshot")
    owner_address = fields.Char(compute="_compute_owner_snapshot")

    odometer_ids = fields.One2many("drivecore.vehicle.odometer", "vehicle_id", string="Odometer History")
    service_visit_ids = fields.One2many("drivecore.service.visit", "vehicle_id", string="Service History")
    sale_order_ids = fields.One2many("sale.order", "drivecore_vehicle_id", string="Sales Orders")
    invoice_ids = fields.One2many("account.move", "drivecore_vehicle_id", string="Invoices")
    pos_order_ids = fields.One2many("pos.order", "drivecore_vehicle_id", string="POS Orders")
    odometer_count = fields.Integer(compute="_compute_counts")
    service_visit_count = fields.Integer(compute="_compute_counts")
    sale_order_count = fields.Integer(compute="_compute_counts")
    invoice_count = fields.Integer(compute="_compute_counts")
    pos_order_count = fields.Integer(compute="_compute_counts")

    _plate_company_unique = models.Constraint(
        "unique(company_id, plate_normalized)",
        "A vehicle with this number plate already exists for the company.",
    )
    _vin_company_unique = models.Constraint(
        "unique(company_id, vin_normalized)",
        "A vehicle with this VIN already exists for the company.",
    )

    @api.depends("year", "make_id.name", "model_id.name", "license_plate")
    def _compute_name(self):
        for vehicle in self:
            vehicle_name = " ".join(
                part for part in [str(vehicle.year or ""), vehicle.make_id.name, vehicle.model_id.name] if part
            )
            vehicle.name = _("%(vehicle)s — %(plate)s", vehicle=vehicle_name, plate=vehicle.license_plate or _("No Plate"))

    @api.depends("license_plate", "vin")
    def _compute_identifiers(self):
        for vehicle in self:
            vehicle.plate_normalized = normalize_identifier(vehicle.license_plate)
            vehicle.vin_normalized = normalize_identifier(vehicle.vin) or False

    @api.depends(
        "partner_id.name",
        "partner_id.phone",
        "partner_id.street",
        "partner_id.street2",
        "partner_id.city",
        "partner_id.state_id.name",
        "partner_id.zip",
        "partner_id.country_id.name",
    )
    def _compute_owner_snapshot(self):
        for vehicle in self:
            partner = vehicle.partner_id
            vehicle.owner_name = partner.name or ""
            vehicle.owner_phone = partner.phone or ""
            vehicle.owner_address = ", ".join(
                part
                for part in [
                    partner.street,
                    partner.street2,
                    partner.city,
                    partner.state_id.name,
                    partner.zip,
                    partner.country_id.name,
                ]
                if part
            )

    @api.depends("odometer_ids", "service_visit_ids", "sale_order_ids", "invoice_ids", "pos_order_ids")
    def _compute_counts(self):
        for vehicle in self:
            vehicle.odometer_count = len(vehicle.odometer_ids)
            vehicle.service_visit_count = len(vehicle.service_visit_ids)
            vehicle.sale_order_count = len(vehicle.sale_order_ids)
            vehicle.invoice_count = len(
                vehicle.invoice_ids.filtered(lambda move: move.move_type in ("out_invoice", "out_refund"))
            )
            vehicle.pos_order_count = len(vehicle.pos_order_ids)

    @api.onchange("make_id")
    def _onchange_make_id(self):
        if self.model_id and self.model_id.make_id != self.make_id:
            self.model_id = False

    @api.constrains("year")
    def _check_year(self):
        current_year = fields.Date.today().year
        for vehicle in self:
            if vehicle.year and not 1886 <= vehicle.year <= current_year + 2:
                raise ValidationError(
                    _("Vehicle year must be between 1886 and %(max_year)s.", max_year=current_year + 2)
                )

    @api.constrains("make_id", "model_id")
    def _check_model_make(self):
        for vehicle in self:
            if vehicle.model_id and vehicle.model_id.make_id != vehicle.make_id:
                raise ValidationError(_("The selected vehicle model does not belong to the selected make."))

    @api.constrains("license_plate", "vin", "company_id")
    def _check_unique_identifiers(self):
        for vehicle in self:
            if vehicle.plate_normalized:
                duplicate = self.search_count([
                    ("id", "!=", vehicle.id),
                    ("company_id", "=", vehicle.company_id.id),
                    ("plate_normalized", "=", vehicle.plate_normalized),
                ])
                if duplicate:
                    raise ValidationError(_("A vehicle with number plate %s already exists.", vehicle.license_plate))
            if vehicle.vin_normalized:
                duplicate = self.search_count([
                    ("id", "!=", vehicle.id),
                    ("company_id", "=", vehicle.company_id.id),
                    ("vin_normalized", "=", vehicle.vin_normalized),
                ])
                if duplicate:
                    raise ValidationError(_("A vehicle with VIN %s already exists.", vehicle.vin))

    def _action_related(self, model, domain, name):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "list,form",
            "domain": domain,
            "context": {"default_drivecore_vehicle_id": self.id, "default_vehicle_id": self.id},
        }

    def action_view_odometer(self):
        return self._action_related(
            "drivecore.vehicle.odometer", [("vehicle_id", "=", self.id)], _("Odometer History")
        )

    def action_view_service_visits(self):
        return self._action_related(
            "drivecore.service.visit", [("vehicle_id", "=", self.id)], _("Service Visits")
        )

    def action_view_sale_orders(self):
        return self._action_related("sale.order", [("drivecore_vehicle_id", "=", self.id)], _("Sales Orders"))

    def action_view_invoices(self):
        return self._action_related("account.move", [("drivecore_vehicle_id", "=", self.id)], _("Invoices"))

    def action_view_pos_orders(self):
        return self._action_related("pos.order", [("drivecore_vehicle_id", "=", self.id)], _("POS Orders"))
