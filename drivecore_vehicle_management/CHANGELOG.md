# Changelog

## 19.0.1.0.2

- Fixed Odoo 19 database-registry initialization failure caused by a dependency on the removed `res.partner.mobile` field.
- Standardized customer telephone handling on Odoo 19's `res.partner.phone` field.
- Updated POS vehicle checkout prefill and backend synchronization to use the supported phone field.
- Retained all vehicle, odometer, service-history, sales-document, invoice, POS, and receipt functionality.
