from odoo import fields, models


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

    def _drivecore_refresh_pos_cache(self):
        """Force Odoo POS clients to discard their previous IndexedDB snapshot."""
        configs = self.sudo().search([])
        if configs:
            configs._compute_local_data_integrity()
        return True
