odoo.define('inmoser_service_order.ServiceOrder', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');

    var ServiceOrderListController = ListController.extend({
        buttons_template: 'inmoser_service_order.buttons',
        events: _.extend({}, ListController.prototype.events, {
            'click .o_button_mass_assign': '_onMassAssign',
        }),

        _onMassAssign: function () {
            var self = this;
            var records = this.getSelectedIds();
            if (records.length === 0) {
                this.do_warn("Please select at least one service order.");
                return;
            }

            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'inmoser.service.order.wizard',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    active_ids: records,
                    default_order_count: records.length,
                },
            });
        },
    });

    var ServiceOrderListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: ServiceOrderListController,
        }),
    });

    viewRegistry.add('service_order_list', ServiceOrderListView);
});
