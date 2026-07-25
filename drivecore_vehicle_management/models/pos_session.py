from odoo import api, models


class PosSession(models.Model):
    _inherit = "pos.session"

    @api.model
    def _load_pos_data_models(self, config):
        models_to_load = super()._load_pos_data_models(config)
        for model_name in [
            "drivecore.vehicle.make",
            "drivecore.vehicle.model",
            "drivecore.service.type",
            "drivecore.vehicle",
        ]:
            if model_name not in models_to_load:
                models_to_load.append(model_name)
        return models_to_load
