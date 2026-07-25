from odoo import fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    drivecore_vehicle_ids = fields.One2many("drivecore.vehicle", "partner_id", string="Vehicles")
    drivecore_vehicle_count = fields.Integer(compute="_compute_drivecore_vehicle_count")

    def _compute_drivecore_vehicle_count(self):
        grouped = self.env["drivecore.vehicle"]._read_group(
            [("partner_id", "in", self.ids)], ["partner_id"], ["__count"]
        )
        counts = {partner.id: count for partner, count in grouped}
        for partner in self:
            partner.drivecore_vehicle_count = counts.get(partner.id, 0)

    def action_view_drivecore_vehicles(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Vehicles"),
            "res_model": "drivecore.vehicle",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
