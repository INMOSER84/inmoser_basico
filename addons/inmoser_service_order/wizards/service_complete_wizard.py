# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ServiceCompleteWizard(models.TransientModel):
    _name = 'inmoser.service.complete.wizard'
    _description = 'Wizard para completar servicio'

    service_order_id = fields.Many2one('inmoser.service.order', required=True, readonly=True)
    diagnosis = fields.Text('Diagnosis', required=True)
    work_performed = fields.Text('Work Performed', required=True)
    photo_before = fields.Binary('Photo Before')
    photo_after = fields.Binary('Photo After')
    customer_signature = fields.Binary('Customer Signature')
    technician_notes = fields.Text('Technician Notes')

    def action_complete_service(self):
        self.ensure_one()
        if self.service_order_id.state != 'in_progress':
            raise UserError(_('Only orders in progress can be completed.'))
        if not self.diagnosis or not self.work_performed:
            raise UserError(_('Diagnosis and work performed are required.'))

        self.service_order_id.write({
            'diagnosis': self.diagnosis,
            'work_performed': self.work_performed,
            'photo_before': self.photo_before,
            'photo_after': self.photo_after,
            'customer_signature': self.customer_signature,
            'technician_notes': self.technician_notes,
            'state': 'done',
            'end_date': fields.Datetime.now(),
        })
        return {'type': 'ir.actions.act_window_close'}
