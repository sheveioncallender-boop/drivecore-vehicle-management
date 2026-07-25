from odoo import api, fields, models


class DriveCoreVehicleMake(models.Model):
    _name = "drivecore.vehicle.make"
    _description = "Vehicle Make"
    _order = "name"
    _inherit = ["pos.load.mixin"]

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    model_ids = fields.One2many("drivecore.vehicle.model", "make_id", string="Models")

    _unique_name = models.Constraint("unique(name)", "This vehicle make already exists.")

    @api.model
    def _load_pos_data_domain(self, data, config):
        return [("active", "=", True)]

    @api.model
    def _load_pos_data_fields(self, config):
        return ["id", "name", "active", "write_date"]
