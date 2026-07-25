from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    drivecore_vehicle_policy = fields.Selection([
        ("optional", "Optional"),
        ("service", "Required for Vehicle-Service Products"),
        ("all", "Required for Every Order"),
    ], default="service", required=True, string="Vehicle Details Policy")
    drivecore_require_customer_name = fields.Boolean(default=True)
    drivecore_require_phone = fields.Boolean(default=True)
    drivecore_require_address = fields.Boolean(default=True)
    drivecore_require_year = fields.Boolean(default=True)
    drivecore_require_make_model = fields.Boolean(default=True)
    drivecore_require_plate = fields.Boolean(default=True)
    drivecore_require_vin = fields.Boolean(default=False)
    drivecore_require_odometer = fields.Boolean(default=True)

    @api.model
    def _load_pos_data_fields(self, config):
        fields_to_load = [
            *super()._load_pos_data_fields(config),
            "drivecore_vehicle_policy",
            "drivecore_require_customer_name",
            "drivecore_require_phone",
            "drivecore_require_address",
            "drivecore_require_year",
            "drivecore_require_make_model",
            "drivecore_require_plate",
            "drivecore_require_vin",
            "drivecore_require_odometer",
        ]
        return list(dict.fromkeys(fields_to_load))

    @api.model
    def _drivecore_refresh_pos_cache(self):
        """Force Odoo POS clients to discard their previous IndexedDB snapshot."""
        configs = self.sudo().search([])
        if configs:
            configs._compute_local_data_integrity()
        return True
