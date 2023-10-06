/** @odoo-module **/
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { session } from "@web/session";

export class OwlDemoTest extends ListController {

    setup() {
        super.setup();
    }


    test() {
       var session = require('web.session');
            console.log("--------------");
            session.rpc('/custom/createdb', {
                    param1 : 'param1'
                 }
            ).then(function() {
                console.log("Creating database");
            }, function () {
                console.log("calling /custom/createdb caused an exception!");
            });
            window.location.reload();
     }

//        this.rpc('/web/dataset/call_kw', {
//            model: this.model,
//            method: 'fill_table_list',
//            kwargs: {},
//        })
         //var Model = require('web.Model')
//         console.log("after Model--------------");
//         var custom_model = new  Model('jrn.tables')
//         console.log("after new Model --------------");
//         custom_model.call('fill_table_list')
//         console.log("after call --------------");
//    }

}

registry.category("views").add("owl_demo_test", {
    ...listView,
    Controller: OwlDemoTest,
    buttonTemplate: "OwlDemoButtons",
});