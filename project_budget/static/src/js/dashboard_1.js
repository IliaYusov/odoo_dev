odoo.define("project_budget.dashboard_1_action", function (require) {
   "use strict";
   var AbstractAction = require('web.AbstractAction');
   var core = require('web.core');
   var QWeb = core.qweb;
   var web_client = require('web.web_client');
   var session = require('web.session');
   var ajax = require('web.ajax');
   var _t = core._t;
   var rpc = require('web.rpc');
   var self = this;
   var DashBoard = AbstractAction.extend({
       contentTemplate: 'dashboard_1',

       init: function(parent, context) {
           this._super(parent, context);
           this.dashboard_templates = ['MainSection'];
       },
       start: function() {
           var self = this;
           this.set("title", 'Dashboard');
           return this._super().then(function() {
               self.render_dashboards();
           });
       },
       willStart: function(){
           var self = this;
           return this._super()
       },
       render_dashboards: function() {
           var self = this;
           this.fetch_data()
           var templates = []
           var templates = ['MainSection'];
           _.each(templates, function(template) {
               self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}))
           });
       },
       fetch_data: function() {
           var self = this
//          fetch data to the tiles
           var def1 = this._rpc({
               model: 'project_budget.project_steps',
               method: "get_data_dashboard_1",
           })
           .then(function (result) {
               $('#etalon_projects').append('<span>' + result.etalon_projects + '</span>');
               $('#current_projects').append('<span>' + result.current_projects + '</span>');
           });
       },
    });
   core.action_registry.add('dashboard_1_tag', DashBoard);
   return DashBoard;
});
