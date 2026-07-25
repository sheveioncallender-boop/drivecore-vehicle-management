/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosOrder.prototype, {
    setup(vals) {
        vals = vals || {};
        super.setup(vals);
        this.drivecore_vehicle_year = vals.drivecore_vehicle_year || 0;
        this.drivecore_vehicle_make = vals.drivecore_vehicle_make || "";
        this.drivecore_vehicle_model = vals.drivecore_vehicle_model || "";
        this.drivecore_number_plate = vals.drivecore_number_plate || "";
        this.drivecore_vin = vals.drivecore_vin || "";
        this.drivecore_odometer = vals.drivecore_odometer ?? null;
        this.drivecore_odometer_unit = vals.drivecore_odometer_unit || "km";
        this.drivecore_odometer_note = vals.drivecore_odometer_note || "";
        this.drivecore_customer_name = vals.drivecore_customer_name || "";
        this.drivecore_customer_phone = vals.drivecore_customer_phone || "";
        this.drivecore_customer_address = vals.drivecore_customer_address || "";
    },

    drivecoreRequiresVehicle() {
        if (this.isRefund) {
            return false;
        }
        const policy = this.config_id?.drivecore_vehicle_policy || "optional";
        if (policy === "optional") {
            return false;
        }
        if (policy === "all") {
            return true;
        }
        return this.lines.some((line) => Boolean(line.product_id?.drivecore_requires_vehicle));
    },

    getDriveCoreMissingFields() {
        const config = this.config_id || {};
        const missing = [];
        if (config.drivecore_require_customer_name && !this.drivecore_customer_name?.trim()) {
            missing.push(_t("Customer name"));
        }
        if (config.drivecore_require_phone && !this.drivecore_customer_phone?.trim()) {
            missing.push(_t("Phone number"));
        }
        if (config.drivecore_require_address && !this.drivecore_customer_address?.trim()) {
            missing.push(_t("Address"));
        }
        if (config.drivecore_require_year && !Number(this.drivecore_vehicle_year)) {
            missing.push(_t("Vehicle year"));
        }
        if (config.drivecore_require_make_model && !this.drivecore_vehicle_make?.trim()) {
            missing.push(_t("Vehicle make"));
        }
        if (config.drivecore_require_make_model && !this.drivecore_vehicle_model?.trim()) {
            missing.push(_t("Vehicle model"));
        }
        if (config.drivecore_require_plate && !this.drivecore_number_plate?.trim()) {
            missing.push(_t("Number plate"));
        }
        if (config.drivecore_require_vin && !this.drivecore_vin?.trim()) {
            missing.push(_t("VIN"));
        }
        const readingMissing =
            this.drivecore_odometer === null ||
            this.drivecore_odometer === "" ||
            Number.isNaN(Number(this.drivecore_odometer)) ||
            Number(this.drivecore_odometer) < 0;
        if (config.drivecore_require_odometer && readingMissing) {
            missing.push(_t("Odometer reading"));
        }
        return missing;
    },

    drivecoreVehicleSummary() {
        const vehicle = [
            this.drivecore_vehicle_year,
            this.drivecore_vehicle_make,
            this.drivecore_vehicle_model,
        ]
            .filter(Boolean)
            .join(" ");
        return this.drivecore_number_plate ? `${vehicle} • ${this.drivecore_number_plate}` : vehicle;
    },
});
