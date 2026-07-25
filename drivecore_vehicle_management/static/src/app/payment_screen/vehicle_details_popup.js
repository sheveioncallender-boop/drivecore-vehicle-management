/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

function partnerAddress(partner) {
    if (!partner) {
        return "";
    }
    return [
        partner.street,
        partner.street2,
        partner.city,
        partner.state_id?.name,
        partner.zip,
        partner.country_id?.name,
    ]
        .filter(Boolean)
        .join(", ");
}

export class DriveCoreVehicleDetailsPopup extends Component {
    static template = "drivecore_vehicle_management.VehicleDetailsPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        order: Object,
        vehicles: Array,
        config: Object,
        getPayload: Function,
        close: Function,
    };

    setup() {
        const order = this.props.order;
        const partner = order.getPartner();
        const selectedVehicleId = order.drivecore_vehicle_id?.id || 0;
        this.state = useState({
            vehicle_id: selectedVehicleId,
            customer_name: order.drivecore_customer_name || partner?.name || "",
            customer_phone:
                order.drivecore_customer_phone || partner?.phone || "",
            customer_address:
                order.drivecore_customer_address || partnerAddress(partner),
            vehicle_year: order.drivecore_vehicle_year || "",
            vehicle_make: order.drivecore_vehicle_make || "",
            vehicle_model: order.drivecore_vehicle_model || "",
            number_plate: order.drivecore_number_plate || "",
            vin: order.drivecore_vin || "",
            odometer: order.drivecore_odometer ?? "",
            odometer_unit: order.drivecore_odometer_unit || "km",
            odometer_note: order.drivecore_odometer_note || "",
            error: "",
        });
    }

    get customerVehicles() {
        const partnerId = this.props.order.getPartner()?.id;
        if (!partnerId) {
            return this.props.vehicles;
        }
        return this.props.vehicles.filter((vehicle) => vehicle.partner_id?.id === partnerId);
    }

    onVehicleChange(event) {
        const vehicleId = Number(event.target.value || 0);
        this.state.vehicle_id = vehicleId;
        if (!vehicleId) {
            return;
        }
        const vehicle = this.props.vehicles.find((item) => item.id === vehicleId);
        if (!vehicle) {
            return;
        }
        this.state.vehicle_year = vehicle.year || "";
        this.state.vehicle_make = vehicle.make_id?.name || "";
        this.state.vehicle_model = vehicle.model_id?.name || "";
        this.state.number_plate = vehicle.license_plate || "";
        this.state.vin = vehicle.vin || "";
        this.state.odometer = vehicle.current_odometer ?? "";
        this.state.odometer_unit = vehicle.odometer_unit || "km";
        this.state.customer_name =
            vehicle.partner_id?.name || vehicle.owner_name || this.state.customer_name;
        this.state.customer_phone =
            vehicle.partner_id?.phone ||
            vehicle.owner_phone ||
            this.state.customer_phone;
        this.state.customer_address =
            partnerAddress(vehicle.partner_id) ||
            vehicle.owner_address ||
            this.state.customer_address;
    }

    _validateRequiredFields() {
        const config = this.props.config || {};
        if (config.drivecore_require_customer_name && !this.state.customer_name.trim()) {
            return _t("Enter the customer name.");
        }
        if (config.drivecore_require_phone && !this.state.customer_phone.trim()) {
            return _t("Enter the customer phone number.");
        }
        if (config.drivecore_require_address && !this.state.customer_address.trim()) {
            return _t("Enter the customer address.");
        }
        if (config.drivecore_require_year && !Number(this.state.vehicle_year)) {
            return _t("Enter the vehicle year.");
        }
        if (config.drivecore_require_make_model && !this.state.vehicle_make.trim()) {
            return _t("Enter the vehicle make.");
        }
        if (config.drivecore_require_make_model && !this.state.vehicle_model.trim()) {
            return _t("Enter the vehicle model.");
        }
        if (config.drivecore_require_plate && !this.state.number_plate.trim()) {
            return _t("Enter the vehicle number plate.");
        }
        if (config.drivecore_require_vin && !this.state.vin.trim()) {
            return _t("Enter the VIN.");
        }
        const odometerMissing =
            this.state.odometer === "" ||
            this.state.odometer === null ||
            Number.isNaN(Number(this.state.odometer)) ||
            Number(this.state.odometer) < 0;
        if (config.drivecore_require_odometer && odometerMissing) {
            return _t("Enter a valid odometer reading.");
        }
        return "";
    }

    confirm() {
        const requiredError = this._validateRequiredFields();
        if (requiredError) {
            this.state.error = requiredError;
            return;
        }

        const year = Number(this.state.vehicle_year || 0);
        const currentYear = new Date().getFullYear();
        if (year && (year < 1886 || year > currentYear + 2)) {
            this.state.error = _t("Enter a valid vehicle year.");
            return;
        }

        const selected = this.props.vehicles.find(
            (vehicle) => vehicle.id === Number(this.state.vehicle_id)
        );
        const newReading = Number(this.state.odometer || 0);
        if (
            selected &&
            newReading < Number(selected.current_odometer || 0) &&
            !this.state.odometer_note.trim()
        ) {
            this.state.error = _t(
                "The odometer is lower than the saved reading. Enter a correction reason."
            );
            return;
        }

        this.props.getPayload({
            vehicle_id: Number(this.state.vehicle_id) || 0,
            customer_name: this.state.customer_name.trim(),
            customer_phone: this.state.customer_phone.trim(),
            customer_address: this.state.customer_address.trim(),
            vehicle_year: year,
            vehicle_make: this.state.vehicle_make.trim(),
            vehicle_model: this.state.vehicle_model.trim(),
            number_plate: this.state.number_plate.trim().toUpperCase(),
            vin: this.state.vin.trim().toUpperCase(),
            odometer: newReading,
            odometer_unit: this.state.odometer_unit,
            odometer_note: this.state.odometer_note.trim(),
        });
        this.props.close();
    }

    cancel() {
        this.props.close();
    }
}
