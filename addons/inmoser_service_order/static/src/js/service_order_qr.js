odoo.define('inmoser_service_order.service_order_qr', function (require) {
'use strict';

var FormController = require('web.FormController');
var FormView = require('web.FormView');
var core = require('web.core');
var Dialog = require('web.Dialog');
var qweb = core.qweb;
var _t = core._t;

var ServiceOrderQRController = FormController.extend({

    /**
     * Renderizar botón QR si el registro está guardado
     */
    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        if (this.modelName === 'inmoser.service.order' && this.renderer.state.res_id) {
            this._addQRButton();
        }
    },

    /**
     * Añadir botón "Ver Código QR"
     */
    _addQRButton: function () {
        var self = this;
        if (this.$buttons) {
            var $qrButton = $('<button/>', {
                type: 'button',
                class: 'btn btn-sm btn-outline-primary ml-2',
                html: '<i class="fa fa-qrcode"/> Ver QR',
                click: function () {
                    self._showQRDialog();
                }
            });
            this.$buttons.find('.o_form_buttons_view').append($qrButton);
        }
    },

    /**
     * Mostrar modal con el código QR
     */
    _showQRDialog: function () {
        var self = this;
        var record = this.model.get(this.handle, {raw: true});
        var orderName = record.data.name;
        var orderID = record.data.id;

        var qrUrl = window.location.origin + '/inmoser/service/' + orderID + '/qr';

        var $content = $(qweb.render('inmoser_service_order.QRDialogContent', {
            orderName: orderName,
            qrUrl: qrUrl
        }));

        new Dialog(this, {
            title: _t('Código QR de la Orden'),
            size: 'medium',
            $content: $content,
            buttons: [
                {
                    text: _t('Imprimir'),
                    classes: 'btn-primary',
                    click: function () {
                        self._printQR($content.find('.qr-img')[0]);
                    }
                },
                {
                    text: _t('Cerrar'),
                    classes: 'btn-secondary',
                    close: true
                }
            ]
        }).open();
    },

    /**
     * Imprimir solo el código QR
     */
    _printQR: function (imgElement) {
        var printWindow = window.open('', '_blank');
        printWindow.document.write('<html><head><title>QR Orden</title></head><body style="text-align:center;">');
        printWindow.document.write('<img src="' + imgElement.src + '" style="max-width:100%;"/>');
        printWindow.document.write('</body></html>');
        printWindow.document.close();
        printWindow.print();
    }

});

var ServiceOrderQRView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
        Controller: ServiceOrderQRController,
    }),
});

// Registrar la vista
core.view_registry.add('service_order_qr_form', ServiceOrderQRView);

return {
    ServiceOrderQRController: ServiceOrderQRController,
    ServiceOrderQRView: ServiceOrderQRView,
};

});
