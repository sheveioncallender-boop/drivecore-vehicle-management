from odoo import api, fields, models


class DriveCoreVehicleModel(models.Model):
    _name = "drivecore.vehicle.model"
    _description = "Vehicle Model"
    _order = "make_id, name"
    _inherit = ["pos.load.mixin"]

    name = fields.Char(required=True, index=True)
    make_id = fields.Many2one("drivecore.vehicle.make", required=True, ondelete="cascade", index=True)
    active = fields.Boolean(default=True)

    _unique_make_model = models.Constraint(
        "unique(make_id, name)", "This vehicle model already exists for the selected make."
    )

    @api.model
    def _load_pos_data_domain(self, data, config):
        return [("active", "=", True)]

    @api.model
    def _load_pos_data_fields(self, config):
        return ["id", "name", "make_id", "active", "write_date"]
