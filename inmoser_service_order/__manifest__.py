{
    "name": "Inmoser Service Order Management",
    "version": "17.0.1.0.0",
    "category": "Services",
    "summary": "Complete service order management system with equipment tracking",
    "description": """
        Comprehensive service order management system for technical services.
        Includes equipment tracking, technician management, customer portal,
        and integration with Odoo native modules.
    """,
    "author": "Inmoser",
    "website": "https://www.inmoser.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "contacts",
        "hr",
        "stock",
        "account",
        "calendar",
        "web",
        "portal"
    ],
    "data": [
        # PRIMERO: Security (DEBE ir primero para crear grupos)
        "security/service_order_security.xml",
        
        # SEGUNDO: Access rules (referencia los grupos creados arriba)
        "security/ir.model.access.csv",
        
        # TERCERO: Datos
        "data/ir_sequence_data.xml",
        "data/service_type_data.xml",
        "data/email_templates.xml",
        
        # CUARTO: Vistas y wizards
        "wizards/service_order_wizard_views.xml",
        "views/res_partner_views.xml",
        "views/hr_employee_views.xml",
        "views/service_equipment_views.xml",
        "views/service_type_views.xml",
        "views/service_order_views.xml",
        "views/service_order_templates.xml",
        "views/service_menu_views.xml",
        "report/service_order_reports.xml"
    ],
    "demo": [
        "demo/service_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "inmoser_service_order/static/src/css/service_order.css",
            "inmoser_service_order/static/src/js/service_order.js",
            "inmoser_service_order/static/src/xml/service_order_templates.xml",
        ],
        "web.assets_qweb": [
            "inmoser_service_order/static/src/xml/**/*",
        ],
        "portal.assets_widgets": [
            "inmoser_service_order/static/src/js/portal.js",
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False
}
