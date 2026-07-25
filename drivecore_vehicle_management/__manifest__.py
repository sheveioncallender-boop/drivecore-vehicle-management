{
    "name": "DriveCore Vehicle Management & POS",
    "version": "19.0.1.0.5",
    "category": "Sales/Point of Sale",
    "summary": "Customer vehicle profiles, odometer history, service records, POS checkout and vehicle details on sales documents",
    "description": """
DriveCore Vehicle Management & POS
==================================
A complete vehicle and service-history application for DriveCore Auto Import & Solutions Limited.

Features include customer vehicle profiles, odometer history, service visits, POS vehicle checkout,
vehicle information on quotations, sales orders, invoices and POS receipts, and service-product rules.
    """,
    "author": "Spxcorp Limited",
    "website": "https://spxcorp.site",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "contacts",
        "product",
        "sale_management",
        "account",
        "point_of_sale"
    ],
    "data": [
        "security/drivecore_security.xml",
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "data/service_type_data.xml",
        "views/vehicle_make_views.xml",
        "views/vehicle_model_views.xml",
        "views/vehicle_views.xml",
        "views/odometer_views.xml",
        "views/service_visit_views.xml",
        "views/res_partner_views.xml",
        "views/product_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "views/pos_order_views.xml",
        "views/pos_config_views.xml",
        "views/service_type_views.xml",
        "views/menus.xml",
        "report/sale_order_report.xml",
        "report/invoice_report.xml"
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "drivecore_vehicle_management/static/src/app/models/pos_order_patch.js",
            "drivecore_vehicle_management/static/src/app/payment_screen/vehicle_details_popup.js",
            "drivecore_vehicle_management/static/src/app/payment_screen/payment_screen_patch.js",
            "drivecore_vehicle_management/static/src/app/payment_screen/vehicle_details_popup.xml",
            "drivecore_vehicle_management/static/src/app/payment_screen/payment_screen_patch.xml",
            "drivecore_vehicle_management/static/src/app/receipt/vehicle_receipt.xml",
            "drivecore_vehicle_management/static/src/scss/drivecore_pos.scss"
        ]
    },
    "images": ["static/description/icon.png"],
    "installable": True,
    "application": True,
    "auto_install": False
}
