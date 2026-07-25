/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

patch(OrderReceipt.prototype, {
    /**
     * Build a plain, receipt-safe object.
     *
     * Keeping all formatting in JavaScript avoids complex expressions in the
     * OWL receipt template, which can fail while the receipt screen renders.
     */
    get drivecoreVehicleReceiptData() {
        const order = this.order;
        if (!order) {
            return { visible: false };
        }

        const vehicleParts = [];
        if (order.drivecore_vehicle_year) {
            vehicleParts.push(String(order.drivecore_vehicle_year));
        }
        if (order.drivecore_vehicle_make) {
            vehicleParts.push(String(order.drivecore_vehicle_make));
        }
        if (order.drivecore_vehicle_model) {
            vehicleParts.push(String(order.drivecore_vehicle_model));
        }

        const partnerName = order.partner_id?.name || "";
        const odometerHasValue =
            order.drivecore_odometer !== null &&
            order.drivecore_odometer !== undefined &&
            order.drivecore_odometer !== "";

        return {
            visible: Boolean(
                order.drivecore_number_plate ||
                    order.drivecore_vin ||
                    vehicleParts.length ||
                    odometerHasValue
            ),
            customerName: order.drivecore_customer_name || partnerName,
            customerPhone: order.drivecore_customer_phone || order.partner_id?.phone || "",
            vehicleName: vehicleParts.join(" "),
            numberPlate: order.drivecore_number_plate || "",
            vin: order.drivecore_vin || "",
            odometer: odometerHasValue ? String(order.drivecore_odometer) : "",
            odometerUnit: order.drivecore_odometer_unit || "km",
        };
    },
});
