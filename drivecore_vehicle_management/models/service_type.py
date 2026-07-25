from odoo import fields, models


class DriveCoreServiceType(models.Model):
    _name = "drivecore.service.type"
    _description = "DriveCore Service Type"
    _order = "sequence, name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text()
    color = fields.Integer()

    _unique_code = models.Constraint("unique(code)", "The service-type code must be unique.")
