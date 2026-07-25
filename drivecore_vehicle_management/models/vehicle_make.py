from odoo import fields, models


class DriveCoreVehicleMake(models.Model):
    _name = "drivecore.vehicle.make"
    _description = "Vehicle Make"
    _order = "name"

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    model_ids = fields.One2many("drivecore.vehicle.model", "make_id", string="Models")

    _unique_name = models.Constraint("unique(name)", "This vehicle make already exists.")
