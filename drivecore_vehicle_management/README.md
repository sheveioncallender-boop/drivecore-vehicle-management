# DriveCore Vehicle Management & POS — Odoo 19

A custom Odoo 19 application for DriveCore Auto Import & Solutions Limited. It keeps each customer's vehicles, odometer history and workshop service records connected to POS, Sales and Invoicing.

## Included features

- Multiple vehicles per customer
- Vehicle year, make, model, number plate, VIN and colour
- Searchable vehicle profiles and customer smart buttons
- Dated odometer history per vehicle
- Lower-reading correction reason and audit trail
- Service visits with technician, findings, work performed and recommendations
- Default service categories:
  - Wheel Alignment
  - Inspection
  - Diagnostics
  - System Check
  - Wheels & Tires
  - Wash & Details
- Vehicle details on quotations, sales orders, customer invoices and credit-note layouts
- POS checkout popup for customer and vehicle details
- Vehicle details on POS orders and thermal receipts
- Configurable POS rule: optional, service products only, or every order
- Automatic vehicle/customer creation from POS checkout when sufficient details are provided
- Automatic odometer and service-history records from confirmed sales, completed POS orders and posted invoices
- Multi-company record rules
- Odoo 19 Community and Enterprise structure

## Installation

1. Copy the `drivecore_vehicle_management` folder into the Odoo custom-addons repository.
2. Commit and deploy the repository to Cloudpepper.
3. Restart/rebuild Odoo so the Python and POS assets are loaded.
4. Update the Apps list.
5. Install **DriveCore Vehicle Management & POS**.

## Initial configuration

1. Open **Settings → Users & Companies → Users**.
2. Assign staff either **Vehicle / Service User** or **Vehicle / Service Manager**.
3. Open **DriveCore Vehicles → Configuration → POS Vehicle Settings**.
4. Choose the vehicle-information policy for each POS configuration.
5. Open each relevant product and use the **DriveCore Service** tab to select a service type and enable **Require Vehicle at POS**.
6. Close and reopen any running POS session after installing or upgrading the module so the new models and frontend assets load.

## Recommended POS policy

Use **Required for Vehicle-Service Products**. Normal retail products can be sold without vehicle details, while workshop-service products require the checkout form.

## Checkout workflow

1. Add service products to the POS order.
2. Open **Customer & Vehicle Details** on the payment screen.
3. Select a saved customer vehicle or enter a new customer and vehicle.
4. Enter the current odometer reading.
5. If the reading is lower than the last saved reading, enter a correction reason.
6. Complete payment. The vehicle, odometer history and service visit are synchronized to the backend.

## Notes

- One quotation, POS order or invoice should represent one vehicle.
- Use separate transactions when one customer brings multiple vehicles.
- For a POS invoice, selecting an existing Odoo customer before payment remains the recommended workflow.
- This module is separate from the DriveCore website module and can be upgraded independently.

## Version 19.0.1.0.2

- Corrected Odoo 19 contact compatibility by using the standard `res.partner.phone` field.
- Removed the obsolete `res.partner.mobile` dependency that prevented database initialization.
- Updated the POS vehicle form and backend order synchronization to use the standard phone value consistently.

## Version 19.0.1.0.4

- Corrected the Odoo 19 POS startup field-loading contract.
- Restored all native POS configuration and order fields, including `use_pricelist` and `currency_id`.
- Kept DriveCore vehicle records out of the initial POS data graph and loads them only when needed.
