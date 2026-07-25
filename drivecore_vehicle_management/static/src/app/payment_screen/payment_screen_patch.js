/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { DriveCoreVehicleDetailsPopup } from "./vehicle_details_popup";

patch(PaymentScreen.prototype, {
    async _loadDriveCoreVehicleChoices() {
        const sessionId = this.pos.session?.id;
        if (!sessionId || this.pos.data.network.offline) {
            return [];
        }
        try {
            return (
                (await this.pos.data.call(
                    "pos.session",
                    "drivecore_get_vehicle_choices",
                    [[sessionId]],
                    {},
                    false
                )) || []
            );
        } catch (error) {
            console.warn("DriveCore vehicle choices could not be loaded", error);
            this.pos.notification.add(
                _t("Existing vehicles could not be loaded. You can still enter the vehicle manually."),
                { type: "warning" }
            );
            return [];
        }
    },

    async openDriveCoreVehicleDetails() {
        const vehicles = await this._loadDriveCoreVehicleChoices();
        const payload = await makeAwaitable(this.dialog, DriveCoreVehicleDetailsPopup, {
            title: _t("Customer & Vehicle Details"),
            order: this.currentOrder,
            vehicles,
            config: this.pos.config,
        });
        if (!payload) {
            return false;
        }

        const order = this.currentOrder;
        const selectedVehicle = payload.vehicle_id
            ? vehicles.find((vehicle) => vehicle.id === payload.vehicle_id) || false
            : false;
        order.drivecore_vehicle_ref = selectedVehicle?.id || 0;

        const selectedPartner = selectedVehicle?.partner_id
            ? this.pos.models["res.partner"].get(selectedVehicle.partner_id)
            : false;
        if (selectedPartner && order.getPartner() !== selectedPartner) {
            order.setPartner(selectedPartner);
        }

        order.drivecore_customer_name = payload.customer_name;
        order.drivecore_customer_phone = payload.customer_phone;
        order.drivecore_customer_address = payload.customer_address;
        order.drivecore_vehicle_year = payload.vehicle_year;
        order.drivecore_vehicle_make = payload.vehicle_make;
        order.drivecore_vehicle_model = payload.vehicle_model;
        order.drivecore_number_plate = payload.number_plate;
        order.drivecore_vin = payload.vin;
        order.drivecore_odometer = payload.odometer;
        order.drivecore_odometer_unit = payload.odometer_unit;
        order.drivecore_odometer_note = payload.odometer_note;
        order._markDirty();
        return true;
    },

    async validateOrder(isForceValidate = false) {
        if (!isForceValidate && this.currentOrder.drivecoreRequiresVehicle()) {
            let missing = this.currentOrder.getDriveCoreMissingFields();
            if (missing.length) {
                await this.openDriveCoreVehicleDetails();
                missing = this.currentOrder.getDriveCoreMissingFields();
                if (missing.length) {
                    this.dialog.add(AlertDialog, {
                        title: _t("Vehicle details required"),
                        body: _t(
                            "Complete the following fields before checkout: %s",
                            missing.join(", ")
                        ),
                    });
                    return;
                }
            }
        }
        return super.validateOrder(...arguments);
    },
});
