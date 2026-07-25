# Changelog

## 19.0.1.0.3
- Fixed POS startup crash where the core `pos.config` record was missing and `currency_id` could not be read.
- Removed DriveCore relational models from the initial POS bootstrap payload.
- Existing vehicles are now loaded lazily when the Vehicle Details dialog opens.
- Added a scalar POS vehicle reference that is resolved to the backend vehicle record during order creation.
- Removed the unused service-type relation from the product POS payload.
- Forced POS cache invalidation during module upgrade.
- Kept manual customer and vehicle entry available when offline.


## 19.0.1.0.2

- Fixed Odoo 19 database-registry initialization failure caused by a dependency on the removed `res.partner.mobile` field.
- Standardized customer telephone handling on Odoo 19's `res.partner.phone` field.
- Updated POS vehicle checkout prefill and backend synchronization to use the supported phone field.
- Retained all vehicle, odometer, service-history, sales-document, invoice, POS, and receipt functionality.
