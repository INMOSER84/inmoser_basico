# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging
import qrcode
import io
import base64
from lxml import etree

_logger = logging.getLogger(__name__)


class ServiceOrder(models.Model):
    _name = 'inmoser.service.order'
    _description = 'Service Order'
    _order = 'name desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    # ------------------------------------------------------------------
    # Campos básicos
    # ------------------------------------------------------------------
    name = fields.Char(
        string='Service Order Number',
        help='Número único de la orden de servicio (OS00001)',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True
    )

    # Relaciones principales
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        domain=[('x_inmoser_is_service_client', '=', True)]
    )

    equipment_id = fields.Many2one(
        'inmoser.service.equipment',
        string='Equipment',
        required=True,
        tracking=True
    )

    service_type_id = fields.Many2one(
        'inmoser.service.type',
        string='Service Type',
        required=True,
        tracking=True
    )

    assigned_technician_id = fields.Many2one(
        'hr.employee',
        string='Assigned Technician',
        domain=[('x_inmoser_is_technician', '=', True)],
        tracking=True
    )

    # Información del servicio
    reported_fault = fields.Text(
        string='Reported Fault',
        help='Falla reportada por el cliente',
        required=True,
        tracking=True
    )

    diagnosis = fields.Text(
        string='Diagnosis',
        help='Diagnóstico técnico del problema',
        tracking=True
    )

    work_performed = fields.Text(
        string='Work Performed',
        help='Descripción del trabajo realizado',
        tracking=True
    )

    # Estados y fechas
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('pending_approval', 'Pending Approval'),
        ('accepted', 'Accepted'),
        ('rescheduled', 'Rescheduled'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True, required=True)

    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        help='Fecha y hora programada para el servicio',
        tracking=True
    )

    start_date = fields.Datetime(
        string='Start Date',
        help='Fecha y hora de inicio real del servicio',
        readonly=True
    )

    end_date = fields.Datetime(
        string='End Date',
        help='Fecha y hora de finalización del servicio',
        readonly=True
    )

    # Aprobación del cliente
    acceptance_status = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], string='Acceptance Status', default='pending', tracking=True)

    customer_signature = fields.Binary(
        string='Customer Signature',
        help='Firma digital del cliente'
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        help='Motivo del rechazo por parte del cliente'
    )

    # Evidencias fotográficas
    photo_before = fields.Binary(
        string='Photo Before',
        help='Evidencia fotográfica antes del servicio'
    )

    photo_after = fields.Binary(
        string='Photo After',
        help='Evidencia fotográfica después del servicio'
    )

    # Información financiera
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True,
        tracking=True,
        help='Monto total del servicio'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        help='Factura generada para este servicio',
        readonly=True
    )

    # Prioridad y configuración
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)

    notes = fields.Text(
        string='Internal Notes',
        help='Notas internas del servicio'
    )

    # Líneas de refacciones
    refaction_line_ids = fields.One2many(
        'inmoser.service.order.refaction.line',
        'order_id',
        string='Refaction Lines',
        help='Refacciones utilizadas en el servicio'
    )

    # Campos computados
    duration = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        help='Duración real del servicio en horas'
    )

    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
        help='Indica si el servicio está atrasado'
    )

    can_start = fields.Boolean(
        string='Can Start',
        compute='_compute_can_start',
        help='Indica si el servicio puede iniciarse'
    )

    refaction_count = fields.Integer(
        string='Refaction Count',
        compute='_compute_refaction_count',
        help='Número de líneas de refacciones'
    )

    # Campos relacionados para facilitar búsquedas
    partner_name = fields.Char(
        related='partner_id.name',
        string='Customer Name',
        readonly=True,
        store=True
    )

    equipment_name = fields.Char(
        related='equipment_id.name',
        string='Equipment Name',
        readonly=True,
        store=True
    )

    technician_name = fields.Char(
        related='assigned_technician_id.name',
        string='Technician Name',
        readonly=True,
        store=True
    )

    # ------------------------------------------------------------------
    # Métodos computados
    # ------------------------------------------------------------------
    @api.depends('refaction_line_ids.total_price', 'service_type_id.base_price')
    def _compute_total_amount(self):
        """Calcula el monto total del servicio"""
        for order in self:
            refaction_total = sum(order.refaction_line_ids.mapped('total_price'))
            base_price = order.service_type_id.base_price if order.service_type_id else 0.0
            order.total_amount = base_price + refaction_total

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """Calcula la duración real del servicio"""
        for order in self:
            if order.start_date and order.end_date:
                diff = order.end_date - order.start_date
                order.duration = diff.total_seconds() / 3600  # Convertir a horas
            else:
                order.duration = 0.0

    @api.depends('scheduled_date', 'state')
    def _compute_is_overdue(self):
        """Determina si el servicio está atrasado"""
        now = fields.Datetime.now()
        for order in self:
            if order.scheduled_date and order.state not in ['done', 'cancelled']:
                order.is_overdue = order.scheduled_date < now
            else:
                order.is_overdue = False

    @api.depends('state', 'assigned_technician_id', 'scheduled_date')
    def _compute_can_start(self):
        """Determina si el servicio puede iniciarse"""
        for order in self:
            order.can_start = (
                order.state == 'assigned' and
                order.assigned_technician_id and
                order.scheduled_date
            )

    @api.depends('refaction_line_ids')
    def _compute_refaction_count(self):
        """Calcula el número de líneas de refacciones"""
        for order in self:
            order.refaction_count = len(order.refaction_line_ids)

    # ------------------------------------------------------------------
    # Crear / Escribir
    # ------------------------------------------------------------------
    @api.model
    def create(self, vals):
        """Override create para generar secuencia automática"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('inmoser.service.order.sequence') or _('New')

        order = super(ServiceOrder, self).create(vals)

        # Crear actividad de seguimiento
        order.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=_('New service order created'),
            note=_('Service order %s has been created and needs to be processed.') % order.name,
            user_id=self.env.user.id
        )

        return order

    def write(self, vals):
        """Override write para tracking de cambios importantes"""
        # Tracking de cambios de estado
        if 'state' in vals:
            for order in self:
                old_state = order.state
                new_state = vals['state']
                if old_state != new_state:
                    order.message_post(
                        body=_('State changed from %s to %s') % (
                            dict(order._fields['state']._description_selection(self.env))[old_state],
                            dict(order._fields['state']._description_selection(self.env))[new_state]
                        )
                    )

        return super(ServiceOrder, self).write(vals)

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Filtra equipos por cliente seleccionado"""
        if self.partner_id:
            return {
                'domain': {
                    'equipment_id': [('partner_id', '=', self.partner_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'equipment_id': []
                }
            }

    @api.onchange('service_type_id')
    def _onchange_service_type_id(self):
        """Actualiza configuración basada en el tipo de servicio"""
        if self.service_type_id:
            # Añadir productos por defecto si los hay
            if self.service_type_id.default_product_ids and not self.refaction_line_ids:
                lines = []
                for product in self.service_type_id.default_product_ids:
                    lines.append((0, 0, {
                        'product_id': product.id,
                        'quantity': 1.0,
                        'unit_price': product.list_price,
                    }))
                self.refaction_line_ids = lines

    # ------------------------------------------------------------------
    # Acciones principales
    # ------------------------------------------------------------------
    def action_assign_technician(self):
        """Acción para asignar técnico y programar servicio"""
        self.ensure_one()

        if not self.assigned_technician_id:
            raise UserError(_('Please select a technician before assigning.'))

        if not self.scheduled_date:
            raise UserError(_('Please set a scheduled date before assigning.'))

        # Verificar disponibilidad del técnico
        if not self.assigned_technician_id.check_daily_capacity(self.scheduled_date.date()):
            raise UserError(_('The selected technician has reached the maximum capacity for this date.'))

        self.state = 'assigned'

        # Crear evento de calendario
        self._create_calendar_event()

        # Enviar notificaciones
        self._send_assignment_notifications()

        return True

    def action_start_service(self):
        """Acción para iniciar el servicio"""
        self.ensure_one()

        if self.state != 'assigned':
            raise UserError(_('Service must be in assigned state to start.'))

        self.write({
            'state': 'in_progress',
            'start_date': fields.Datetime.now()
        })

        return True

    def action_request_approval(self):
        """Acción para solicitar aprobación del cliente"""
        self.ensure_one()

        if self.state != 'in_progress':
            raise UserError(_('Service must be in progress to request approval.'))

        if not self.diagnosis:
            raise UserError(_('Please provide a diagnosis before requesting approval.'))

        self.state = 'pending_approval'

        # Enviar notificación al cliente
        self._send_approval_request()

        return True

    def action_customer_accept(self):
        """Acción para aceptación del cliente"""
        self.ensure_one()

        self.write({
            'acceptance_status': 'accepted',
            'state': 'accepted'
        })

        # Reservar refacciones
        for line in self.refaction_line_ids:
            line.reserve_stock()

        return True

    def action_customer_reject(self):
        """Acción para rechazo del cliente"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Rejection Reason'),
            'res_model': 'inmoser.service.order.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }

    def action_complete_service(self):
        """Acción para completar el servicio"""
        self.ensure_one()

        if self.state != 'accepted':
            raise UserError(_('Service must be accepted to complete.'))

        if not self.work_performed:
            raise UserError(_('Please describe the work performed before completing.'))

        # Consumir refacciones del inventario
        for line in self.refaction_line_ids:
            line.consume_stock()

        self.write({
            'state': 'done',
            'end_date': fields.Datetime.now()
        })

        # Odoo es un sistema que funciona a través de llamadas de método y acciones.
        # Si un botón en la interfaz de usuario está configurado para llamar a un método específico, ese método debe existir.
        # Si un botón con la etiqueta 'action_generate_invoice' existe en la vista XML de Odoo, la función debe ser definida en el modelo
        # por lo que si se hace clic en ese botón, Odoo intentará ejecutar un método llamado action_generate_invoice.

        # Para que tu lógica funcione, necesitas el método público action_generate_invoice
        # y puedes llamar a la función _generate_invoice

        return True

    def action_view_refactions(self):
        """
        Action to open a tree view of the refaction lines for the current service order.
        """
        self.ensure_one()
        return {
            'name': _('Refactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'inmoser.service.order.refaction.line',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

    def action_generate_invoice(self):
        """
        Genera una factura para la orden de servicio y redirige a la vista de la factura.
        Este método es una acción de usuario que se llama desde la interfaz.
        """
        self.ensure_one()
        invoice = self._generate_invoice()
        if invoice:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Generated Invoice'),
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_reschedule(self):
        """Acción para reprogramar el servicio"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reschedule Service'),
            'res_model': 'inmoser.service.order.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }

    def action_cancel(self):
        """Acción para cancelar el servicio"""
        self.ensure_one()

        # Cancelar reservas de refacciones
        for line in self.refaction_line_ids:
            line.cancel_reservation()

        self.state = 'cancelled'

        return True

    def action_view_qr(self):
        """Mostrar QR real en modal"""
        self.ensure_one()

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        qr_text = f"{base_url}/inmoser/service-order/{self.id}"

        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(qr_text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        def fields_view_get(self_, view_id=None, view_type='form', toolbar=False, submenu=False):
            res = super(ServiceOrder, self_).fields_view_get(view_id=view_id, view_type=view_type,
                                                             toolbar=toolbar, submenu=submenu)
            if view_type == 'form' and self_.env.context.get('qr_image'):
                doc = etree.XML(res['arch'])
                for image in doc.xpath("//image"):
                    image.set('filename', 'QR.png')
                    image.text = self_.env.context['qr_image']
                res['arch'] = etree.tostring(doc, encoding='unicode')
            return res

        self.fields_view_get = fields_view_get

        return {
            'type': 'ir.actions.act_window',
            'name': 'Service Order QR',
            'res_model': 'inmoser.service.order',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': dict(self.env.context, qr_image=qr_base64),
            'res_id': self.id,
        }

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------
    def _create_calendar_event(self):
        """Crea evento de calendario para el servicio"""
        self.ensure_one()

        if not self.scheduled_date or not self.assigned_technician_id:
            return

        # Calcular duración estimada
        duration = self.service_type_id.estimated_duration if self.service_type_id else 2.0
        end_date = self.scheduled_date + timedelta(hours=duration)

        event_vals = {
            'name': f"Service: {self.name} - {self.partner_id.name}",
            'start': self.scheduled_date,
            'stop': end_date,
            'description': f"""
Service Order: {self.name}
Customer: {self.partner_id.name}
Equipment: {self.equipment_id.name}
Reported Fault: {self.reported_fault}
            """,
            'partner_ids': [(6, 0, [self.partner_id.id])],
            'user_id': self.assigned_technician_id.user_id.id if self.assigned_technician_id.user_id else False,
        }

        self.env['calendar.event'].create(event_vals)

    def _send_assignment_notifications(self):
        """Envía notificaciones de asignación"""
        self.ensure_one()

        # Notificar al técnico
        if self.assigned_technician_id and self.assigned_technician_id.user_id:
            self.message_subscribe(partner_ids=[self.assigned_technician_id.user_id.partner_id.id])
            self.message_post(
                body=_('Service order assigned to technician %s for %s') % (
                    self.assigned_technician_id.name,
                    self.scheduled_date.strftime('%Y-%m-%d %H:%M')
                ),
                partner_ids=[self.assigned_technician_id.user_id.partner_id.id]
            )

        # Notificar al cliente (si tiene usuario)
        if self.partner_id.user_ids:
            self.message_post(
                body=_('Your service order %s has been scheduled for %s') % (
                    self.name,
                    self.scheduled_date.strftime('%Y-%m-%d %H:%M')
                ),
                partner_ids=[self.partner_id.id]
            )

    def _send_approval_request(self):
        """Envía solicitud de aprobación al cliente"""
        self.ensure_one()

        # Crear enlace para aprobación del cliente
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        approval_url = f"{base_url}/my/service_orders/{self.id}/approve"

        body = _("""
        <p>Dear %s,</p>
        <p>Our technician has diagnosed your equipment and is ready to proceed with the service.</p>
        <p><strong>Diagnosis:</strong> %s</p>
        <p><strong>Estimated Cost:</strong> %s %s</p>
        <p>Please review and approve the service by clicking <a href="%s">here</a>.</p>
        """) % (
            self.partner_id.name,
            self.diagnosis or _('No diagnosis provided'),
            self.total_amount,
            self.currency_id.name,
            approval_url
        )

        self.message_post(
            body=body,
            partner_ids=[self.partner_id.id],
            subject=_('Service Approval Required - %s') % self.name
        )

    def _generate_invoice(self):
        """Genera factura para el servicio"""
        self.ensure_one()

        if self.invoice_id:
            return self.invoice_id

        # Crear factura
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_origin': self.name,
            'ref': self.name,
            'invoice_line_ids': []
        }

        # Línea de servicio base
        if self.service_type_id.base_price > 0:
            invoice_line_vals = {
                'name': f"Service: {self.service_type_id.name}",
                'quantity': 1,
                'price_unit': self.service_type_id.base_price,
                'account_id': self.env['account.account'].search([
                    ('user_type_id.name', '=', 'Income')
                ], limit=1).id,
            }
            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Líneas de refacciones
        for line in self.refaction_line_ids:
            invoice_line_vals = {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
                'account_id': line.product_id.property_account_income_id.id or
                                 line.product_id.categ_id.property_account_income_categ_id.id,
            }
            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id

        return invoice

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """Valida que la fecha programada sea futura"""
        for order in self:
            if order.scheduled_date and order.scheduled_date < fields.Datetime.now():
                if order.state == 'draft':  # Solo validar en borrador
                    raise ValidationError(_('Scheduled date must be in the future.'))

    # ------------------------------------------------------------------
    # name_get / name_search
    # ------------------------------------------------------------------
    def name_get(self):
        """Personaliza la visualización del nombre de la orden"""
        result = []
        for order in self:
            name = order.name or ''
            if order.partner_id:
                name += f" - {order.partner_id.name}"
            if order.equipment_id:
                name += f" ({order.equipment_id.equipment_type})"
            result.append((order.id, name))
        return result

    @api.model
    def get_technician_workload(self, technician_id, date_from, date_to):
        """
        Obtiene la carga de trabajo de un técnico en un período

        Args:
            technician_id (int): ID del técnico
            date_from (datetime): Fecha de inicio
            date_to (datetime): Fecha de fin

        Returns:
            dict: Información de carga de trabajo
        """
        orders = self.search([
            ('assigned_technician_id', '=', technician_id),
            ('scheduled_date', '>=', date_from),
            ('scheduled_date', '<=', date_to),
            ('state', 'not in', ['cancelled', 'done'])
        ])

        # El método está incompleto, faltaría la lógica para procesar las órdenes
        # y devolver la información de carga de trabajo.

    def get_state_label(self):
        """Texto traducido del estado"""
        return dict(self._fields['state']._description_selection(self.env))[self.state]

    def get_state_badge_class(self):
        """Clase Bootstrap para el badge de estado"""
        mapping = {
            'draft': 'badge-secondary',
            'assigned': 'badge-info',
            'in_progress': 'badge-primary',
            'pending_approval': 'badge-warning',
            'accepted': 'badge-light',
            'rescheduled': 'badge-dark',
            'done': 'badge-success',
            'cancelled': 'badge-danger',
        }
        return 'badge ' + mapping.get(self.state, 'badge-secondary')

    def get_priority_label(self):
        """Texto traducido de la prioridad"""
        return dict(self._fields['priority']._description_selection(self.env))[self.priority]

    def get_priority_badge_class(self):
        """Clase Bootstrap para el badge de prioridad"""
        mapping = {
            'low': 'badge-secondary',
            'normal': 'badge-info',
            'high': 'badge-warning',
            'urgent': 'badge-danger',
        }
        return 'badge ' + mapping.get(self.priority, 'badge-secondary')

    def get_progress_percentage(self):
        """Porcentaje de progreso para la barra de progreso"""
        progress_map = {
            'draft': 0,
            'assigned': 25,
            'in_progress': 50,
            'pending_approval': 75,
            'accepted': 85,
            'rescheduled': 15,
            'done': 100,
            'cancelled': 0,
        }
        return progress_map.get(self.state, 0)
