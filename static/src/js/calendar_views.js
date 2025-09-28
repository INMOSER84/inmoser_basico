odoo.define('inmoser_service_order.calendar_views', function (require) {
    "use strict";

    var CalendarView = require('web.CalendarView');
    var CalendarRenderer = require('web.CalendarRenderer');
    var CalendarModel = require('web.CalendarModel');
    var viewRegistry = require('web.view_registry');

    var ServiceOrderCalendarModel = CalendarModel.extend({
        // Extender el modelo si es necesario
    });

    var ServiceOrderCalendarRenderer = CalendarRenderer.extend({
        // Extender el renderizador si es necesario
    });

    var ServiceOrderCalendarView = CalendarView.extend({
        config: _.extend({}, CalendarView.prototype.config, {
            Model: ServiceOrderCalendarModel,
            Renderer: ServiceOrderCalendarRenderer,
        }),
    });

    viewRegistry.add('service_order_calendar', ServiceOrderCalendarView);

    return {
        ServiceOrderCalendarModel: ServiceOrderCalendarModel,
        ServiceOrderCalendarRenderer: ServiceOrderCalendarRenderer,
        ServiceOrderCalendarView: ServiceOrderCalendarView,
    };
});
