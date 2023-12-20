from odoo import Command, fields, models


class DocumentFlowProcessingWizardResume(models.TransientModel):
    _name = 'document_flow.processing.wizard.resume'
    _description = 'Document Flow Processing Wizard: Resume'

    comment = fields.Html(string='Comment')

    def action_resume_processing(self):
        self.ensure_one()
        process = self.env['document_flow.processing'].browse(
            self.env.context.get('active_id', False)).process_ids.filtered(lambda pr: pr.state == 'break')[:1]
        if process:
            process.resume_from_last_stage(description=self.comment)

        return None

    def action_start_processing_again(self):
        self.ensure_one()

        processing_id = self.env['document_flow.processing'].browse(self.env.context.get('active_id', False))
        if processing_id:
            process = self.env['document_flow.process'].create(dict(
                type='complex',
                template_id=processing_id.template_id.id,
                name=processing_id.name,
                description=processing_id.parent_ref.description,
                company_ids=processing_id.parent_ref.company_id if not processing_id.parent_ref._fields.get(
                    'company_ids', False) else processing_id.parent_ref.company_ids
            ))
            main_processes = dict()
            for action in processing_id.action_ids:
                simple_process = self.env['document_flow.process'].create({
                    'name': action.name,
                    'type': action.type,
                    'parent_id': process.id,
                    'task_sequence': action.task_sequence,
                    'sequence': action.sequence,
                    'reviewer_ref': action.reviewer_ref,
                    'start_condition': action.start_condition,
                    'description': action.description,
                    'action_id': action.id,
                    'return_on_process_id': False if not action.return_on_action_id else main_processes.get(
                        action.return_on_action_id.id).id,
                    'company_ids': [Command.link(c_id) for c_id in action._get_executors_company_ids()]
                })
                main_processes[action.id] = simple_process
                for child in action.child_ids:
                    pr = self.env['document_flow.process'].create({
                        'name': child.name,
                        'type': child.type,
                        'parent_id': simple_process.id,
                        'task_sequence': child.task_sequence,
                        'sequence': child.sequence,
                        'reviewer_ref': child.reviewer_ref,
                        'start_condition': child.start_condition,
                        'description': child.description,
                        'action_id': child.id,
                        'return_on_process_id': False if not action.return_on_action_id else self.env[
                            'document_flow.process'].search(['action_id', '=', child.id], limit=1).id,
                        'company_ids': [Command.link(c_id) for c_id in action._get_executors_company_ids()]
                    })
                    for executor in child.executor_ids:
                        self.env['document_flow.process.executor'].create({
                            'process_id': pr.id,
                            'sequence': executor.sequence,
                            'type_sequence': executor.type_sequence,
                            'executor_ref': '%s,%s' % (type(executor.executor_ref).__name__, executor.executor_ref.id),
                            'period': executor.period
                        })
                for executor in action.executor_ids:
                    self.env['document_flow.process.executor'].create({
                        'process_id': simple_process.id,
                        'sequence': executor.sequence,
                        'type_sequence': executor.type_sequence,
                        'executor_ref': '%s,%s' % (type(executor.executor_ref).__name__, executor.executor_ref.id),
                        'period': executor.period
                    })
            processing_id.process_ids = [Command.link(process.id)]
            process.action_start_process()

        return None
