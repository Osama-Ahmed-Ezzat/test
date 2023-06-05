# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date


class SalaryScale(models.Model):
    _name = 'salary.scale'
    _description = 'Salary Scale'

    name = fields.Char("Name")
    year = fields.Char("Year")
    no_of_steps = fields.Integer("No Of Steps")
    step_name_type = fields.Selection([('number', 'Number'), ('alphabet', 'Alphabet')],string="Numbering Method",default='number')
    annual_increase_ratio = fields.Float("Annual Increase Ratio")
    cost_of_living = fields.Float("Cost Of Living")
    type_of_increase = fields.Selection([('number', 'In Fixed Number'), ('ratio', 'In Ratio')],string="Type Of Increase",default='number')
    in_ratio = fields.Float("Ratio")
    in_number = fields.Float("Amount")
    increase_amount = fields.Float("Increase Amount")
    max_step_for_new_hire = fields.Char("Maximum Steps For New Hires")
    start_date = fields.Date()
    end_date = fields.Date()
    general_ratio_id = fields.Many2one('general.ratio', "General Ratio")
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')],string="State",default='draft')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    number_digits = fields.Integer(string="Number Digits",)
    parent_scale_id = fields.Many2one('salary.scale')
    type_of_increase_id = fields.One2many('salary.scale.typeof.increase','scale_id',store=True,readonly=False,compute='_onchange_type_of_increase_id')
    is_gss_scale = fields.Boolean(string="Is GSS Scale")

    @api.depends('is_gss_scale')
    def _onchange_type_of_increase_id(self):
        for rec in self:
                if rec.is_gss_scale:
                    rec.write({'type_of_increase_id':[(5, 0, 0)]})
                    if rec.parent_scale_id:
                        if rec.parent_scale_id.type_of_increase_id:
                            for i in rec.parent_scale_id.type_of_increase_id:
                                rec.write({'type_of_increase_id': [(0, 0, {'scale_id':rec.id,'name':i.name,'type_of_increase':i.type_of_increase
                                                                   ,'in_ratio':i.in_ratio,'in_number':i.in_number,'max_step_for_increase':i.max_step_for_increase
                                                                   })]})


    # Constrains To Avoid Duplication And No.of Steps >0
    @api.constrains("no_of_steps","name","year")
    def check_no_of_steps(self):
        for rec in self:
            lst = rec.year.split("/")
            if len(lst) == 1:
                raise ValidationError("Year should be in format '2021/2022'")
            if rec.no_of_steps <= 0:
                raise ValidationError(_('No.of Steps Must Be Greater Than 0!!'))
            all_record_ids = self.search([('id','!=',self.id)])
            if all_record_ids:
                for record in all_record_ids:
                    if record.name == self.name and record.year == self.year:
                        # raise ValidationError(_('You Can Not Create Salary Scale Record With Same Name In Same Year!!'))
                        pass
    # Approve Button Function

    def get_record(self, name, scale_id):
        """Search for a record based on name and scale_id"""
        record = self.env['salary.scale.typeof.increase'].search([
            ('name', '=', name),
            ('scale_id', '=', scale_id),
        ], limit=1)
        return record
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            current_year = self.general_ratio_id.year
            lst = current_year.split("/")
            # search_year = str((int(lst[0]) - 1)) + '/' + str(lst[0])
            # last_salary_scale = self.search([('year','=',search_year)],limit=1)
            last_salary_scale = self.search([('id','=',self.parent_scale_id.id)],limit=1)
            if last_salary_scale:
                jobs = self.env['salary.steps.placement'].search([('scale_id','=',last_salary_scale.id)])
                # print('jobs',jobs)


                for job in jobs:
                    last_salary_steps = self.env['salary.steps'].search([('placement_id','=',job.id),
                                                                        ('scale_id','=',last_salary_scale.id)],order='amount')
                    last_created_record = self.env['salary.steps'].search([('step', 'in',['A','1','a']),('placement_id','=',job.id),],
                                                                          order='create_date desc', limit=1)

                    # print(last_salary_steps)
                    # print(last_created_record)
                    # last_incr_amount = self.env['salary.steps'].search([('placement_id','=',job.id),
                    #                                                     ('scale_id','=',last_salary_scale.id)],order='create_date, step',limit=2)


                    # print('last_salary_steps[0].last_placement_increase_amount')
                    # print(last_salary_steps[0].last_placement_increase_amount)
                    # raise ValidationError('last_salary_steps')
                    # print(last_incr_amount)
                    last_incr_amount_diff = last_salary_steps[0].last_placement_increase_amount
                    net_last_incr_amount_diff = last_salary_steps[0].last_placement_increase_net_amount
                    # print('last_incr_amount_diff',last_incr_amount_diff)
                    # for zz in last_salary_steps:
                    #     print({'amount':zz.amount,
                    #           'step':zz.step,
                    #
                    #           })
                    type_of_inc = self.get_record(last_created_record.scale_type_of_increase.name,self.id)
                    print(type_of_inc)
                    print(type_of_inc.name)
                    print(type_of_inc.total_amount)
                    # print('last_salary_steps',last_salary_steps)
                    first_step = last_salary_steps[0]
                    # Inside the 'for job in jobs' loop

                    # Calculate the percentage increase if annual_increase_ratio is not 0
                    increase_ratio = (
                                first_step.amount * self.cost_of_living / 100) if self.cost_of_living != 0 else 0
                    net_increase_ratio = (
                                first_step.net_amount * self.cost_of_living / 100) if self.cost_of_living != 0 else 0

                    if rec.currency_id.symbol == 'EGP':
                        step = self.env['salary.steps'].create({
                            'scale_id': self.id,
                            'year': self.year,
                            'placement_id': job.id,
                            'scale_type_of_increase': type_of_inc.id,
                            'amount':  first_step.amount + increase_ratio,
                            'net_amount': first_step.net_amount + net_increase_ratio,
                            'last_placement_increase_amount': last_incr_amount_diff,
                        })
                    print(first_step.net_amount)
                    print(net_increase_ratio,)
                    raise ValidationError('55555555555555555555555555555')

                    if rec.currency_id.symbol == '$':
                        step = self.env['salary.steps'].create({
                            'scale_id': self.id,
                            'year': self.year,
                            'placement_id': job.id,
                            'amount':  first_step.amount + increase_ratio,
                            'net_amount':first_step.net_amount + net_increase_ratio,
                            'scale_type_of_increase': first_step.scale_type_of_increase.id,
                            'last_placement_increase_amount': last_incr_amount_diff,
                            'last_placement_increase_net_amount': net_last_incr_amount_diff
                        })

                    # print({'amount': first_step.amount + (first_step.amount * self.annual_increase_ratio / 100),
                    #        'net_amount': first_step.net_amount + (
                    #                first_step.net_amount * self.annual_increase_ratio / 100)})
                    job.step_ids |= step
                    for emp in self.env['hr.employee'].search([('salary_placement_id','=',job.id)]):

                        if emp.salary_step_id:

                            if emp.salary_step_id.scale_id.step_name_type == 'number':
                                next_step = int(emp.salary_step_id.step) + 1
                            else:

                                next_step = chr(ord(emp.salary_step_id.step) + 1)
                            new_step = self.env['salary.steps'].search([('scale_id','=',self.id),('placement_id','=',job.id),('step','=',next_step)])

                            if new_step:

                                emp.salary_step_id = new_step
                        if emp.contract_id:

                            # emp.contract_id.state = 'close'
                            contract_id = emp.contract_id.sudo().copy()
                            contract_id.employee_id = False
                            contract_id.employee_id = emp.id

                            contract_id.state = 'draft'
                            contract_id.renewed = True
                            contract_id.date_end = rec.end_date
                            contract_id.date_start = rec.start_date
                    for step in last_salary_steps:
                        step.active = False

    # Onchange Function Of General Ratio To Auto Assign Values
    @api.onchange("general_ratio_id")
    def _onchange_general_ratio_id(self):
        for rec in self:
            rec.year = rec.general_ratio_id and rec.general_ratio_id.year or ''
            rec.annual_increase_ratio = rec.general_ratio_id and rec.general_ratio_id.annual_increase_ratio or 0.0
            rec.cost_of_living = rec.general_ratio_id and rec.general_ratio_id.cost_of_living or 0.0

    # Scheduler Action Function For Create 
    def salary_scale_creation(self):
        current_year = todays_date = date.today().year
        last_digits = int(current_year)%100
        prev_year_digit = last_digits-1
        search_year = str(prev_year_digit) + '/' + str(last_digits)
        new_general_ratio_id = False
        last_general_ratio_ids = self.env['general.ratio'].search([('state','=','approved'),('year','=',search_year)])
        if last_general_ratio_ids:
            for last_general_ratio_id in last_general_ratio_ids:
                year = last_general_ratio_id.year
                lst = year.split("/")
                next_year = lst[1] + '/' + str((int(lst[1])+1))
                new_general_ratio_id = self.env['general.ratio'].create({
                        'year': next_year,
                        'annual_increase_ratio': last_general_ratio_id.annual_increase_ratio,
                        'cost_of_living': last_general_ratio_id.cost_of_living,
                    })

        last_salary_scale_ids = self.search([('state','=','approved'),('year','=',search_year)])
        if last_salary_scale_ids:
            for last_salary_scale_id in last_salary_scale_ids:
                if last_salary_scale_id.year:
                    year = last_salary_scale_id.year
                    lst = year.split("/")
                    next_year = lst[1] + '/' + str((int(lst[1])+1))
                    new_salary_scale_id = self.create({
                        'name':last_salary_scale_id.name or '',
                        'year': next_year,
                        'general_ratio_id': new_general_ratio_id and new_general_ratio_id.id or False,
                        'no_of_steps': last_salary_scale_id.no_of_steps,
                        'step_name_type': last_salary_scale_id.step_name_type,
                        'annual_increase_ratio': last_salary_scale_id.annual_increase_ratio,
                        'cost_of_living': last_salary_scale_id.cost_of_living,
                        'type_of_increase': last_salary_scale_id.type_of_increase,
                        'in_ratio': last_salary_scale_id.in_ratio,
                        'in_number': last_salary_scale_id.in_number,
                        'max_step_for_new_hire': last_salary_scale_id.max_step_for_new_hire,
                    })
                    new_salary_scale_id._onchange_general_ratio_id()
                    last_employee_job_ids = self.env['employee.job'].search([('scale_id','=',last_salary_scale_id.id)])
                    if last_employee_job_ids:
                        for last_employee_job_id in last_employee_job_ids:
                            new_job_id = self.env['employee.job'].create({
                                'name': last_employee_job_id.name,
                                'scale_id': new_salary_scale_id and new_salary_scale_id.id,
                            })

                            if last_employee_job_id and last_employee_job_id.step_ids:
                                new_amount = 0
                                new_net_amount = 0
                                first_step = 0
                                for step in last_employee_job_id.step_ids:
                                    if last_salary_scale_id.type_of_increase == 'ratio':
                                        if first_step<1:
                                            new_amount = step.amount * ((last_salary_scale_id.annual_increase_ratio/100)+1)*((last_salary_scale_id.cost_of_living/100)+1)
                                            new_net_amount = step.net_amount * ((last_salary_scale_id.annual_increase_ratio/100)+1)*((last_salary_scale_id.cost_of_living/100)+1)
                                            first_step += 1
                                    elif last_salary_scale_id.type_of_increase == 'number':
                                        new_amount = new_salary_scale_id.in_number
                                        new_net_amount = new_salary_scale_id.in_number
                                    new_amount_tot =  step.amount + new_amount
                                    new_net_amount_tot =  step.net_amount + new_net_amount
                                    self.env['salary.steps'].create({
                                        'step':step.step,
                                        'amount':new_amount_tot,
                                        'net_amount':new_net_amount_tot,
                                        'job_id': new_job_id.id
                                    })



class SalaryIncreaseTypes(models.Model):
    _name = 'salary.scale.typeof.increase'
    name = fields.Char('name')
    type_of_increase = fields.Selection([('number', 'In Fixed Number'), ('ratio', 'In Ratio')],string="Type Of Increase",default='number')
    in_ratio = fields.Float("Ratio")
    in_number = fields.Float("Amount")
    increase_amount = fields.Float("Increase Amount")
    scale_id = fields.Many2one('salary.scale')
    total_amount = fields.Float("Total Amount",store=True,compute='get_total_amount')
    max_step_for_increase = fields.Char("Maximum Steps For Increase")
    senior_rate = fields.Float("Senior Rate")
    @api.depends('increase_amount','type_of_increase','scale_id','in_number','in_ratio','scale_id.cost_of_living')
    def get_total_amount(self):
        for rec in self:
            total = rec.in_number
            cost = 0.0
            if rec.scale_id.cost_of_living:
                if rec.type_of_increase == 'number':
                    cost = rec.in_number * (rec.scale_id.cost_of_living/100)

            rec.total_amount = total + cost
    # placement_id = fields.Many2one('salary.steps.placement','Placement')