from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta

class commercial_budget(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'project_budget.commercial_budget'
    _description = "project_commercial budget"
    _rec_name = 'name_to_show'

    name = fields.Char(string="commercial_budget name", required=True)
    budget_state = fields.Selection([('work', 'Working'), ('fixed', 'Fixed')], required=True, index=True, default='work', copy = False, tracking=True)
    etalon_budget = fields.Boolean(string="etalon_budget", default = False)
    date_actual = fields.Datetime(string="Actuality date", index=True, copy=False)
    year = fields.Integer(string="Budget year", required=True, index=True,default=2023)
    currency_id = fields.Many2one('res.currency', string='Account Currency')
    descr = fields.Text( string='Description', default="")
    name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')
    projects_ids = fields.One2many(
        comodel_name='project_budget.projects',
        inverse_name='commercial_budget_id',
        string="commercial_budget specification",
        copy=True, auto_join=True)

    def _get_name_to_show(self):
        for commercial_budget in self:
            if commercial_budget.date_actual:
                commercial_budget.name_to_show = commercial_budget.name + ' (' + commercial_budget.budget_state + ' ' + commercial_budget.date_actual.strftime("%d-%m-%Y") + ')'
            else:
                commercial_budget.name_to_show = commercial_budget.name + ' (' + commercial_budget.budget_state+')'

    def isuseradmin(self):
        self.ensure_one()
        return self.env.ref('project_budget.project_budget_admin')

    @api.constrains('year')
    def _check_date_end(self):
        for record in self:
            if record.year < 2022 or record.year > 2030:
                raisetext = _("The year must be between 2022-2030")
                raise ValidationError(raisetext)

    def get_user_datetime(self):
        fmt = "%Y-%m-%d %H:%M:%S"
        tz = pytz.timezone(self.env.user.tz) or pytz.utc
        now_time = fields.datetime.now(tz=tz)
        my_dt = fields.datetime.strptime(now_time.strftime(fmt), fmt)
        return my_dt

    def set_budget_fixed(self):
        if not self.user_has_groups('project_budget.project_budget_admin'):
            raisetext=_("Only users in group project_budget.project_budget_admin can set budget to fixed")
            raise (ValidationError(raisetext))
        else:
            if self.budget_state == 'fixed':
                raisetext = _("Only working budget can be duplicated")
            self.ensure_one()
            # self.budget_state='fixed'
            # self.date_actual = fields.datetime.now()
            cur_datetime = self.get_user_datetime()
            print('cur_datetime=', cur_datetime)
            newbudget = self.env['project_budget.commercial_budget'].sudo().browse(self.id).copy({
                'budget_state': 'fixed',
                'date_actual': fields.datetime.now(),
            })
            print('after copy')

            # меняем parent_id в скопированных проектах
            child_projects = self.env['project_budget.projects'].sudo().search(['&',
                                                                                ('parent_project_id', '!=', False),
                                                                                ('commercial_budget_id', '=', newbudget.id),
                                                                                ])
            for child_project in child_projects:
                print('child_project', child_project)
                child_project.parent_project_id = (self.env['project_budget.projects']
                                                   .sudo().search(['&',
                                                                   ('project_id', '=', child_project.parent_project_id.project_id),
                                                                   ('commercial_budget_id', '=', newbudget.id),
                                                                   ]))

            activity_type_for_approval = self.env.ref('project_budget.mail_act_send_project_to_supervisor_for_approval').id
            activity_type_approve_supervisor = self.env.ref('project_budget.mail_act_approve_project_by_supervisor').id
            res_model_id_project_budget = self.env['ir.model'].search([('model', '=', 'project_budget.projects')]).id
            print('activity_type_for_approval ')
            activity_model = self.env['mail.activity']
            for spec in self.sudo().projects_ids:
                print('spec project_id = ', spec.project_id)
                print('spec.with_context was_changes')

                spec.was_changes = False
                if spec.stage_id.code in ('0', '100(done)'):
                    print('spec.with_context spec.approve_state')
                    spec.approve_state = "-"

                    # Use the search method to find the activities that need to be marked as done
                    activities = activity_model.sudo().search([('res_id', '=', spec.id),
                                                        ('activity_type_id', 'in', (activity_type_for_approval,activity_type_approve_supervisor))
                                                        ])
                    for activitie in activities:
                        activitie.sudo().action_done()

                if spec.stage_id.code in ('10','30','50','75','100'):

                    # Get a reference to the mail.activity model
                    # Use the search method to find the activities that need to be marked as done

                    activities = activity_model.sudo().search([('res_id', '=', spec.id),
                                                        ('activity_type_id', 'in', (activity_type_for_approval,activity_type_approve_supervisor))
                                                        ])
                    # Update the state of each activity to 'done'
                    for activitie in activities:
                        activitie.sudo().action_done()

                    print('spec.with_context spec.approve_state')
                    spec.approve_state = 'need_approve_manager'

                    self.env['mail.activity'].sudo().create({
                        'display_name': _('Need send to supervisor for approval'),
                        'summary': _('You need send to supervisor for approval'),
                        'date_deadline': fields.datetime.now(),
                        'user_id': spec.project_manager_id.user_id.id,
                        'res_id': spec.id,
                        'res_model_id': res_model_id_project_budget,
                        'activity_type_id': activity_type_for_approval
                    })
                # вот далее обновляем ссылки на step в созданных проектах, хотя может просто как то модель можно изменить... я ХЗ
            for project in newbudget.sudo().projects_ids:
                print('project_id = ', project.project_id)
                if project.project_have_steps:
                    for planned_cash_flow in project.planned_cash_flow_ids:
                        current_project = self.env['project_budget.project_steps'].sudo().search(
                            [('projects_id', '=', project.id),('step_id','=',planned_cash_flow.project_steps_id.step_id)])
                        planned_cash_flow.project_steps_id = current_project.id
                    for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                        current_project = self.env['project_budget.project_steps'].sudo().search(
                            [('projects_id', '=', project.id), ('step_id', '=', planned_acceptance_flow.project_steps_id.step_id)])
                        planned_acceptance_flow.project_steps_id = current_project.id
                    for fact_cash_flow in project.fact_cash_flow_ids:
                        current_project = self.env['project_budget.project_steps'].sudo().search(
                            [('projects_id', '=', project.id), ('step_id', '=', fact_cash_flow.project_steps_id.step_id)])
                        fact_cash_flow.project_steps_id = current_project.id
                    for fact_acceptance_flow in project.fact_acceptance_flow_ids:
                        current_project = self.env['project_budget.project_steps'].sudo().search(
                            [('projects_id', '=', project.id), ('step_id', '=', fact_acceptance_flow.project_steps_id.step_id)])
                        fact_acceptance_flow.project_steps_id = current_project.id

                for fact_acceptance_flow in project.fact_acceptance_flow_ids: # у нас на распределение (distribution) ссылается плановые и фактические данные и при копировании у фрейма крутит голову. потому вручную ссылка на плановое поступеление в распределенеии ставим
                    for distribution_acceptance in fact_acceptance_flow.distribution_acceptance_ids: # идем по распределению, привязанному к факту  - копирование оставили тоолько у факта для фрейма
                        if distribution_acceptance.planned_acceptance_flow_id.acceptance_id: # берем acceptance_id  и по нему ищем в новом бюдете запись
                            new_planned_acceptance = self.env['project_budget.planned_acceptance_flow'].sudo().search(
                                [('projects_id', '=', project.id),
                                 ('acceptance_id', '=', distribution_acceptance.planned_acceptance_flow_id.acceptance_id)])
                            if new_planned_acceptance: # нулевые записи не копируются
                                distribution_acceptance.planned_acceptance_flow_id = new_planned_acceptance.id # ставим ссылку на скопированную зщапись в распределениии
                for fact_cash_flow in project.fact_cash_flow_ids: # у нас на распределение (distribution) ссылается плановые и фактические данные и при копировании у фрейма крутит голову. потому вручную ссылка на плановое поступеление в распределенеии ставим
                    for distribution_cash in fact_cash_flow.distribution_cash_ids: # идем по распределению, привязанному к факту  - копирование оставили тоолько у факта для фрейма
                        if distribution_cash.planned_cash_flow_id.cash_id: # берем cash_id  и по нему ищем в новом бюдете запись
                            new_planned_cash = self.env['project_budget.planned_cash_flow'].sudo().search(
                                [('projects_id', '=', project.id),
                                 ('cash_id', '=', distribution_cash.planned_cash_flow_id.cash_id)])
                            if new_planned_cash: # нулевые записи не копируются
                                distribution_cash.planned_cash_flow_id = new_planned_cash.id # ставим ссылку на скопированную зщапись в распределениии

            # self.env['project_budget.projects'].search([('project_id', '=', self.id)]).write({'approve_state': 'need_approve_manager'})
            # meeting_act_type = self.env['mail.activity.type'].search([('category', '=', 'meeting')], limit=1)
            # if not meeting_act_type:
            #     meeting_act_type = self.env['mail.activity.type'].create({
            #         'name': 'Meeting Test',
            #         'category': 'meeting',
            #     })

            return False

    def set_budget_work(self):
        self.ensure_one()
        working_budgets = self.env['project_budget.commercial_budget'].search([('budget_state', '=', 'work')])
        if len(working_budgets) > 0 :
            raisetext = _("Already exists budget in work!")
            raise (ValidationError(raisetext))
        else:
            if not self.user_has_groups('project_budget.project_budget_admin'):
                raisetext =_("Only users in group project_budget.project_budget_admin can return budget to work")
                raise (ValidationError(raisetext))
            else:
                self.budget_state='work'
                self.date_actual=None
                return False

