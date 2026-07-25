from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def drivecore_get_vehicle_choices(self):
        """Return flat vehicle choices without extending the POS startup model graph.

        Loading custom relational models during POS bootstrap can make the entire
        startup payload fail. This method is called only when the cashier opens
        the vehicle-details dialog, and returns plain dictionaries.
        """
        self.ensure_one()
        vehicles = self.env["drivecore.vehicle"].search(
            [
                ("active", "=", True),
                ("company_id", "=", self.company_id.id),
            ],
            order="license_plate, year desc",
            limit=2000,
        )
        return [
            {
                "id": vehicle.id,
                "display_name": vehicle.display_name,
                "partner_id": vehicle.partner_id.id,
                "owner_name": vehicle.partner_id.name or "",
                "owner_phone": vehicle.partner_id.phone or "",
                "owner_address": vehicle.partner_id.contact_address or "",
                "year": vehicle.year or 0,
                "make_name": vehicle.make_id.name or "",
                "model_name": vehicle.model_id.name or "",
                "license_plate": vehicle.license_plate or "",
                "vin": vehicle.vin or "",
                "odometer_unit": vehicle.odometer_unit or "km",
                "current_odometer": vehicle.current_odometer or 0.0,
            }
            for vehicle in vehicles
        ]
