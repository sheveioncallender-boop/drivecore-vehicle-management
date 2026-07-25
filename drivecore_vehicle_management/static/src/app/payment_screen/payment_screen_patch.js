/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { DriveCoreVehicleDetailsPopup } from "./vehicle_details_popup";

patch(PaymentScreen.prototype, {
    async openDriveCoreVehicleDetails() {
        const model = this.pos.models["drivecore.vehicle"];
        const vehicles = model?.getAll?.() || [];
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
        order.drivecore_vehicle_id = selectedVehicle;
        if (selectedVehicle?.partner_id && order.getPartner() !== selectedVehicle.partner_id) {
            order.setPartner(selectedVehicle.partner_id);
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
