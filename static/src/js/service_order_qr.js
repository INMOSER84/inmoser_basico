odoo.define('inmoser_service_order.service_order_qr', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var framework = require('web.framework');
    var session = require('web.session');

    var _t = core._t;

    var ServiceOrderQR = {
        init: function () {
            this.setupQRCodes();
        },

        setupQRCodes: function () {
            var self = this;
            $(document).on('click', '.o_service_order_qr_button', function (e) {
                e.preventDefault();
                var orderId = $(this).data('order-id');
                self.showQRCode(orderId);
            });
        },

        showQRCode: function (orderId) {
            var self = this;
            self._rpc({
                model: 'service.order',
                method: 'read',
                args: [[orderId], ['name', 'partner_id', 'qr_code']],
            }).then(function (result) {
                if (result.length > 0) {
                    var order = result[0];
                    var $content = $(QWeb.render('service_order_qr_modal', {
                        service_order_name: order.name,
                        customer_name: order.partner_id[1],
                        qr_code_image: 'data:image/png;base64,' + order.qr_code,
                    }));

                    var dialog = new Dialog(self, {
                        title: _t("Service Order QR Code"),
                        size: 'medium',
                        $content: $content,
                        buttons: [
                            {
                                text: _t("Download"),
                                classes: 'btn-primary',
                                click: function () {
                                    self.downloadQRCode(order.qr_code, order.name);
                                },
                            },
                            {
                                text: _t("Close"),
                                close: true,
                            },
                        ],
                    }).open();
                }
            });
        },

        downloadQRCode: function (qrCode, orderName) {
            var link = document.createElement('a');
            link.href = 'data:image/png;base64,' + qrCode;
            link.download = 'QR_Code_' + orderName + '.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },
    };

    core.bus.on('web_client_ready', null, function () {
        ServiceOrderQR.init();
    });

    return ServiceOrderQR;
});
