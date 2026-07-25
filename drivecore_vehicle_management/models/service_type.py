from odoo import api, fields, models


class DriveCoreServiceType(models.Model):
    _name = "drivecore.service.type"
    _description = "DriveCore Service Type"
    _order = "sequence, name"
    _inherit = ["pos.load.mixin"]

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text()
    color = fields.Integer()

    _unique_code = models.Constraint("unique(code)", "The service-type code must be unique.")

    @api.model
    def _load_pos_data_domain(self, data, config):
        return [("active", "=", True)]

    @api.model
    def _load_pos_data_fields(self, config):
        return ["id", "name", "code", "sequence", "active", "write_date"]
