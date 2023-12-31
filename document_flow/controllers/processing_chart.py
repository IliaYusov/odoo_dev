from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class ProcessingChartController(http.Controller):

    #TODO: sudo для доступа к задачам? Аунется в форме истории
    def _prepare_process_data(self, process):
        return dict(
            id=process.id,
            name=process.name,
            date_end=process.date_end,
            tasks=[self._prepare_task_data(task) for task in process.sudo().task_ids],
            link='/mail/view?model=%s&res_id=%s' % ('document_flow.process', process.id),
            state='done' if process.state == 'finished' else 'cancel' if process.state == 'break' else 'todo'
        )

    def _prepare_task_data(self, task):
        return dict(
            id=task.id,
            name=task.name,
            is_closed=task.is_closed,
            date_closed=task.date_closed or '',
            execution_result=task.execution_result,
            executor=', '.join(task.user_ids.mapped('name')) or '',
            actual_executor=task.actual_executor_id.name or '',
            link='/mail/view?model=%s&res_id=%s' % ('task.task', task.id)
        )

    @http.route('/document_flow/get_processing_chart', type='json', auth='user')
    def get_process_chart(self, process_id, **kw):
        process = request.env['document_flow.process'].browse(process_id)
        if not process:
            return {
                'main_processes': [],
                'sub_processes': []
            }

        values = dict(
            self=self._prepare_process_data(process),
            main_processes=[self._prepare_process_data(process.parent_id)],
            sub_processes=[self._prepare_process_data(child) for child in process.child_ids if child != process]
        )
        return values

    @http.route('/document_flow/get_process_chart', type='json', auth='user')
    def get_process_chart_new(self, process_id, **kw):
        process = request.env['document_flow.process'].browse(process_id)
        if not process:
            return {
                'sub_processes': []
            }

        values = dict(
            self=self._prepare_process_data(process),
            sub_processes=[self._prepare_process_data(child) for child in
                           process.child_ids.filtered(lambda pr: pr.state != 'skipped') if child != process]
        )
        return values
