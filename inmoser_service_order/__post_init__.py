def _post_init_hook(cr, registry):
    """Post initialization hook for the module"""
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Create default service types if they don't exist
    default_service_types = [
        ('PREVENTIVE', 'Preventive Maintenance'),
        ('CORRECTIVE', 'Corrective Maintenance'),
        ('INSTALLATION', 'Installation'),
        ('CALIBRATION', 'Calibration'),
        ('EMERGENCY', 'Emergency Service')
    ]
    
    for code, name in default_service_types:
        if not env['inmoser.service.type'].search([('code', '=', code)], limit=1):
            env['inmoser.service.type'].create({
                'code': code,
                'name': name,
                'sequence': 10
            })
    
    # Set up default access rights
    env['ir.model.access'].search([
        ('model_id.model', 'in', [
            'inmoser.service.order',
            'inmoser.service.equipment',
            'inmoser.service.type',
            'inmoser.service.order.refaction.line'
        ])
    ]).unlink()
