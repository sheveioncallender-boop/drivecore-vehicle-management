# Changelog

## 19.0.1.0.6
- Fixed the OWL receipt-screen crash after validating a POS order.
- Moved vehicle receipt formatting into a receipt component getter.
- Removed complex QWeb expressions from the receipt template.
- Added safe fallbacks for customer, vehicle and odometer values.


## 19.0.1.0.4
- Fixed the POS bootstrap `use_pricelist` failure and the follow-on `currency_id` JavaScript error.
- Removed the custom `pos.config._load_pos_data_fields()` override. In Odoo 19, the core POS config deliberately loads all configuration fields; narrowing that list removed required core fields.
- Removed the custom `pos.order._load_pos_data_fields()` override for the same Odoo 19 compatibility reason.
- Removed DriveCore vehicle, make, model and service-type models from the automatic POS bootstrap graph. Existing vehicles continue to load only when the cashier opens the vehicle-details dialog.
- Preserved product-level `drivecore_requires_vehicle` loading, vehicle checkout, odometer history and receipt functionality.
- Refreshed POS local-data integrity during upgrade.

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

## 19.0.1.0.5
- Removed the invalid no-argument XML `<function>` call used during module upgrades.
- Prevents `ValueError: not enough values to unpack` while loading `pos_cache_refresh.xml`.
- POS browser cache should be cleared manually after deployment to discard old IndexedDB data.
