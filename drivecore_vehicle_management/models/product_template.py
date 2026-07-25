from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    drivecore_service_type_id = fields.Many2one("drivecore.service.type", string="Vehicle Service Type")
    drivecore_requires_vehicle = fields.Boolean(
        string="Require Vehicle at POS",
        help="When this product is sold in POS, the configured vehicle-information rule is enforced.",
    )

    @api.onchange("drivecore_service_type_id")
    def _onchange_drivecore_service_type(self):
        if self.drivecore_service_type_id:
            self.drivecore_requires_vehicle = True


class ProductProduct(models.Model):
    _inherit = "product.product"

    drivecore_service_type_id = fields.Many2one(
        related="product_tmpl_id.drivecore_service_type_id", store=True, readonly=True
    )
    drivecore_requires_vehicle = fields.Boolean(
        related="product_tmpl_id.drivecore_requires_vehicle", store=True, readonly=True
    )

    @api.model
    def _load_pos_data_fields(self, config):
        fields_to_load = [
            *super()._load_pos_data_fields(config),
            "drivecore_requires_vehicle",
        ]
        return list(dict.fromkeys(fields_to_load))
