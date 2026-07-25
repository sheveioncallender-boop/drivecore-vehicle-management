from odoo import fields, models


class DriveCoreVehicleModel(models.Model):
    _name = "drivecore.vehicle.model"
    _description = "Vehicle Model"
    _order = "make_id, name"

    name = fields.Char(required=True, index=True)
    make_id = fields.Many2one("drivecore.vehicle.make", required=True, ondelete="cascade", index=True)
    active = fields.Boolean(default=True)

    _unique_make_model = models.Constraint(
        "unique(make_id, name)", "This vehicle model already exists for the selected make."
    )
