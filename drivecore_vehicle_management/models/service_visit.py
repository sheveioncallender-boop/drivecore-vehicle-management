from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DriveCoreServiceVisit(models.Model):
    _name = "drivecore.service.visit"
    _description = "DriveCore Service Visit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "visit_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(default=lambda self: _("New"), copy=False, readonly=True, index=True)
    visit_date = fields.Datetime(default=fields.Datetime.now, required=True, index=True, tracking=True)
    state = fields.Selection([
        ("draft", "Booked"),
        ("in_progress", "In Progress"),
        ("done", "Completed"),
        ("cancel", "Cancelled"),
    ], default="draft", required=True, tracking=True, index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True, tracking=True)
    vehicle_id = fields.Many2one(
        "drivecore.vehicle", required=True, ondelete="restrict", index=True, tracking=True, check_company=True
    )
    service_type_ids = fields.Many2many("drivecore.service.type", string="Services")
    odometer = fields.Float(tracking=True)
    odometer_unit = fields.Selection(related="vehicle_id.odometer_unit", readonly=True)
    odometer_note = fields.Text(string="Odometer Correction Reason")
    customer_request = fields.Text()
    technician_findings = fields.Text()
    work_performed = fields.Text()
    recommendations = fields.Text()
    technician_id = fields.Many2one("res.users", string="Technician")
    sale_order_id = fields.Many2one("sale.order", ondelete="set null", index=True)
    pos_order_id = fields.Many2one("pos.order", ondelete="set null", index=True)
    invoice_id = fields.Many2one("account.move", ondelete="set null", index=True)
    odometer_record_id = fields.Many2one("drivecore.vehicle.odometer", readonly=True, ondelete="set null")

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            self.partner_id = self.vehicle_id.partner_id
            self.company_id = self.vehicle_id.company_id
            self.odometer = self.vehicle_id.current_odometer

    @api.constrains("vehicle_id", "partner_id")
    def _check_vehicle_owner(self):
        for visit in self:
            if visit.vehicle_id and visit.partner_id != visit.vehicle_id.partner_id:
                raise ValidationError(_("The service-visit customer must be the vehicle owner."))

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = sequence.next_by_code("drivecore.service.visit") or _("New")
            vehicle = self.env["drivecore.vehicle"].browse(vals.get("vehicle_id")).exists()
            if vehicle:
                vals.setdefault("partner_id", vehicle.partner_id.id)
                vals.setdefault("company_id", vehicle.company_id.id)
        records = super().create(vals_list)
        records._create_odometer_records()
        return records

    def write(self, vals):
        if self.env.context.get("skip_drivecore_visit_history"):
            return super().write(vals)
        result = super().write(vals)
        if {"odometer", "vehicle_id", "visit_date", "odometer_note"} & set(vals):
            self._create_odometer_records()
        return result

    def _create_odometer_records(self):
        Odometer = self.env["drivecore.vehicle.odometer"]
        for visit in self.filtered(lambda record: record.vehicle_id and record.odometer is not False):
            source_record = Odometer
            if visit.pos_order_id:
                source_record = Odometer.search([("pos_order_id", "=", visit.pos_order_id.id)], limit=1)
            elif visit.sale_order_id:
                source_record = Odometer.search([("sale_order_id", "=", visit.sale_order_id.id)], limit=1)
            elif visit.invoice_id:
                source_record = Odometer.search([("invoice_id", "=", visit.invoice_id.id)], limit=1)

            if source_record:
                link_vals = {"service_visit_id": visit.id}
                if visit.odometer_note:
                    link_vals["lower_reading_reason"] = visit.odometer_note
                source_record.write(link_vals)
                if visit.odometer_record_id != source_record:
                    visit.with_context(skip_drivecore_visit_history=True).write({
                        "odometer_record_id": source_record.id,
                    })
                continue

            odometer_vals = {
                "vehicle_id": visit.vehicle_id.id,
                "reading": visit.odometer,
                "reading_date": visit.visit_date,
                "source": "service",
                "service_visit_id": visit.id,
            }
            if visit.odometer_note:
                odometer_vals["lower_reading_reason"] = visit.odometer_note
            if visit.odometer_record_id:
                visit.odometer_record_id.write(odometer_vals)
            else:
                odometer = Odometer.create(odometer_vals)
                visit.with_context(skip_drivecore_visit_history=True).write({
                    "odometer_record_id": odometer.id,
                })

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_reset_draft(self):
        self.write({"state": "draft"})
