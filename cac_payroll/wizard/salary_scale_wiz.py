# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import ValidationError

def letter_to_number(letters):
    letters = letters.lower()
    dic = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 4,
        "e": 5,
        "f": 6,
        "g": 7,
        "h": 8,
        "i": 9,
        "j": 10,
        "k": 11,
        "l": 12,
        "m": 13,
        "n": 14,
        "o": 15,
        "p": 16,
        "q": 17,
        "r": 18,
        "s": 19,
        "t": 20,
        "u": 21,
        "v": 22,
        "w": 23,
        "x": 24,
        "y": 25,
        "z": 26,
    }
    return dic.get(letters)

class SalaryScaleWiz(models.TransientModel):
    _name = 'salary.scale.wiz'

    general_ratio_id = fields.Many2one('general.ratio', "General Ratio")

    def button_salary_scale_creation(self):
        for rec in self:
            active_id = self.env.context.get('active_id')
            active_record = self.env['salary.scale'].search([('id', '=', active_id)])
            if active_record and self.general_ratio_id.year:
                year = self.general_ratio_id.year
                lst = year.split("/")
                # next_year = lst[1] + '/' + str((int(lst[1]) + 1))
                # exit_salary_scale_record_id = self.env['salary.scale'].search(
                #     [('state', '=', 'approved'), ('year', '=', self.general_ratio_id.year)])
                # if exit_salary_scale_record_id:
                #     # raise ValidationError(_('You Can Not Create Salary Scale Record With Same Name In Same Year!!'))
                #     pass
                # else:
                current_year = self.general_ratio_id.year
                lst = current_year.split("/")

                # search_year = str((int(lst[0]) - 1)) + '/' + str(lst[0])
                if active_record.year:
                    new_salary_scale_id = self.env['salary.scale'].create({
                        'name': active_record.name or '',
                        'year': current_year,
                        'general_ratio_id': rec.general_ratio_id and rec.general_ratio_id.id or False,
                        'no_of_steps': active_record.no_of_steps,
                        'step_name_type': active_record.step_name_type,
                        'annual_increase_ratio': rec.general_ratio_id.annual_increase_ratio,
                        'cost_of_living': rec.general_ratio_id.cost_of_living,
                        'type_of_increase': active_record.type_of_increase,
                        'in_ratio': active_record.in_ratio,
                        'is_gss_scale':active_record.is_gss_scale,
                        'in_number': active_record.in_number,
                        'max_step_for_new_hire': active_record.max_step_for_new_hire,
                        'parent_scale_id': active_record.id,
                        'currency_id':active_record.currency_id.id
                        # 'max_step_for_increase':active_record.max_step_for_increase

                    })

                    # typofincr = self.env['salary.scale.typeof.increase'].search([('scale_id','=',active_record.id)])
                    # for i in typofincr:
                    #     new_salary_scale_id.type_of_increase_id = [(4, i.id, False)]

                    last_salary_steps_ids = self.env['salary.steps'].search([('scale_id', '=', active_record.id)])
                    job_list = []
                    if last_salary_steps_ids:
                        for step in last_salary_steps_ids:
                            if step.placement_id not in job_list:
                                job_list.append(step.placement_id)
                        increase_amount = 0
                        increase_net_amount = 0

                        step_amount = 0
                        step_net_amount = 0
                        first_step_amount = 0
                        first_net_amount = 0
                        last_step_amount = 0
                        last_net_amount = 0
                        gss_step_amount = 0
                        gss_step_net_amount = 0
                        index = 1
                        if job_list:
                            for job in job_list:
                                if job.step_ids:
                                    for job_step in job.step_ids:
                                        last_incr_amount = self.env['salary.steps'].search(
                                            [('placement_id', '=', job_step.placement_id.id),
                                             ('scale_id', '=', job_step.scale_id.id)],
                                            order='create_date, step', limit=2)
                                        for zz in last_incr_amount:
                                            print(zz.placement_id.name)
                                            print({'amount': zz.amount,
                                                'net_amount': zz.net_amount,
                                                   'step': zz.step,

                                                   })
                                        last_incr_amount_diff = last_incr_amount[1].amount - \
                                                                last_incr_amount[0].amount
                                        net_last_incr_amount_diff = last_incr_amount[1].net_amount - \
                                                                    last_incr_amount[0].net_amount

                                        if job_step.scale_id.id == active_record.id:
                                            if job_step.step == '1' or job_step.step == 'A':
                                                # raise ValidationError('Job step')
                                                if not job_step.scale_id.is_gss_scale:
                                                    first_step_amount = job_step.amount * (
                                                                (rec.general_ratio_id.annual_increase_ratio / 100) + 1) * ((rec.general_ratio_id.cost_of_living / 100) + 1)
                                                    first_net_amount = job_step.net_amount * (
                                                                  (rec.general_ratio_id.cost_of_living / 100) + 1)

                                                    step_amount = first_step_amount
                                                    step_net_amount = first_net_amount

                                                    print("step_net_amount",step_net_amount)
                                                    print("step_amount",step_amount)
                                                    print("index",index)
                                                    self.env['salary.steps'].with_context(force_create=True).create({
                                                        'step': job_step.step,
                                                        'scale_id': job_step.scale_id.id or False,
                                                        'year': current_year,
                                                        'amount': first_step_amount,
                                                        'net_amount': first_net_amount,
                                                        'placement_id': job_step.placement_id and job_step.placement_id.id or False,
                                                        'last_placement_increase_amount': last_incr_amount_diff,
                                                        'last_placement_increase_net_amount': net_last_incr_amount_diff
                                                    })
                                                else:
                                                    raise ValidationError('Job step 2')

                                                    first_step_amount = job_step.amount * (
                                                            (rec.general_ratio_id.annual_increase_ratio / 100) + 1) * ((
                                                                                                                                   rec.general_ratio_id.cost_of_living / 100) + 1)
                                                    first_net_amount = job_step.net_amount * (
                                                            (rec.general_ratio_id.annual_increase_ratio / 100) + 1) * ((
                                                                                                                                   rec.general_ratio_id.cost_of_living / 100) + 1)

                                                    step_amount = first_step_amount
                                                    step_net_amount = first_net_amount

                                                    self.env['salary.steps'].with_context(force_create=True).create({
                                                        'step': job_step.step,
                                                        'scale_id': job_step.scale_id.id or False,
                                                        'scale_type_of_increase': job_step.scale_type_of_increase.id or False,
                                                        'year': current_year,
                                                        'amount': first_step_amount,
                                                        'net_amount': first_net_amount,
                                                        'placement_id': job_step.placement_id and job_step.placement_id.id or False,
                                                        'last_placement_increase_amount': last_incr_amount_diff,
                                                        'last_placement_increase_net_amount': net_last_incr_amount_diff
                                                    })
                                            else:

                                                if not job_step.scale_id.is_gss_scale:
                                                    if job_step.scale_id.type_of_increase == 'ratio':
                                                        if job_step.scale_type_of_increase.max_step_for_increase:
                                                            if job_step.step < job_step.scale_type_of_increase.max_step_for_increase:

                                                                increase_amount = first_step_amount * (
                                                                            job_step.scale_id.in_ratio / 100)
                                                                increase_net_amount = first_net_amount * (
                                                                            job_step.scale_id.in_ratio / 100)
                                                                step_amount += increase_amount
                                                                step_net_amount += increase_net_amount
                                                        else:
                                                            increase_amount = first_step_amount * (
                                                                    job_step.scale_id.in_ratio / 100)
                                                            increase_net_amount = first_net_amount * (
                                                                    job_step.scale_id.in_ratio / 100)
                                                            step_amount += increase_amount
                                                            step_net_amount += increase_net_amount
                                                    elif job_step.scale_id.type_of_increase == 'number':
                                                        index = index +1
                                                        print('step_amount --------',step_amount)
                                                        if job_step.scale_type_of_increase.max_step_for_increase:
                                                            if (job_step.step) < int(job_step.scale_type_of_increase.max_step_for_increase):
                                                                increase_amount = new_salary_scale_id.in_number
                                                                increase_net_amount = new_salary_scale_id.in_number
                                                                step_amount += increase_amount
                                                                step_net_amount += increase_net_amount
                                                        else:
                                                            increase_amount = new_salary_scale_id.in_number
                                                            increase_net_amount = new_salary_scale_id.in_number
                                                            step_amount += increase_amount
                                                            step_net_amount += increase_net_amount
                                                    self.env['salary.steps'].with_context(force_create=True).create({
                                                        'step': job_step.step,
                                                        'scale_id': job_step.scale_id.id or False,
                                                        'year': current_year,
                                                        'amount': step_amount,
                                                        'net_amount': step_net_amount,
                                                        'placement_id': job_step.placement_id and job_step.placement_id.id or False,
                                                        'last_placement_increase_amount': last_incr_amount_diff,
                                                        'last_placement_increase_net_amount': net_last_incr_amount_diff
                                                    })
                                                    print({'step_amount':step_amount,'net_amount':step_net_amount,'last_placement_increase_net_amount'
                                                           :net_last_incr_amount_diff
                                                           })
                                                else:
                                                    if job_step.scale_type_of_increase.type_of_increase == 'ratio':
                                                        if job_step.scale_type_of_increase.max_step_for_increase:
                                                            last_incr_amount = self.env['salary.steps'].search(
                                                                [('placement_id', '=', job_step.placement_id.id),
                                                                 ('scale_id', '=', job_step.scale_id.id)],
                                                                order='create_date, step', limit=2)
                                                            for zz in last_incr_amount:
                                                                print({'amount':zz.amount,
                                                                      'step':zz.step,

                                                                      })
                                                            raise ValidationError('22222222222222222222222222222222')
                                                            last_incr_amount_diff = last_incr_amount[1].amount - \
                                                                                    last_incr_amount[0].amount
                                                            net_last_incr_amount_diff = last_incr_amount[1].net_amount - \
                                                                                    last_incr_amount[0].net_amount
                                                            if job_step.step.isnumeric():
                                                                if int(job_step.step) <= int(job_step.scale_type_of_increase.max_step_for_increase):
                                                                    increase_amount = first_step_amount * (
                                                                                job_step.scale_type_of_increase.in_ratio / 100)
                                                                    increase_net_amount = first_net_amount * (
                                                                                job_step.scale_type_of_increase.in_ratio / 100)
                                                                    step_amount += increase_amount
                                                                    step_net_amount += increase_net_amount
                                                                    gss_step_amount = step_amount
                                                                    gss_step_net_amount = step_net_amount
                                                                else:

                                                                    # increase_amount = job_step.scale_type_of_increase.in_number
                                                                    # increase_net_amount = job_step.scale_type_of_increase.in_number
                                                                    step_amount = gss_step_amount + last_incr_amount_diff
                                                                    step_net_amount = gss_step_net_amount + net_last_incr_amount_diff
                                                            else:
                                                                if letter_to_number(job_step.step) <= int(job_step.scale_type_of_increase.max_step_for_increase):
                                                                    increase_amount = first_step_amount * (
                                                                            job_step.scale_type_of_increase.in_ratio / 100)
                                                                    increase_net_amount = first_net_amount * (
                                                                            job_step.scale_type_of_increase.in_ratio / 100)
                                                                    step_amount += increase_amount
                                                                    step_net_amount += increase_net_amount
                                                                    gss_step_amount = step_amount
                                                                    gss_step_net_amount = step_net_amount
                                                                else:
                                                                    # increase_amount = job_step.scale_type_of_increase.in_number
                                                                    # increase_net_amount = job_step.scale_type_of_increase.in_number
                                                                    step_amount = gss_step_amount + last_incr_amount_diff
                                                                    step_net_amount = gss_step_net_amount + net_last_incr_amount_diff
                                                        else:
                                                            increase_amount = first_step_amount * (
                                                                    job_step.scale_type_of_increase.in_ratio / 100)
                                                            increase_net_amount = first_net_amount * (
                                                                    job_step.scale_type_of_increase.in_ratio / 100)
                                                            step_amount += increase_amount
                                                            step_net_amount += increase_net_amount
                                                    elif job_step.scale_type_of_increase.type_of_increase == 'number':
                                                        if job_step.scale_type_of_increase.max_step_for_increase:
                                                            last_incr_amount = self.env['salary.steps'].search(
                                                                [('placement_id', '=', job_step.placement_id.id),
                                                                 ('scale_id', '=', job_step.scale_id.id)],
                                                                order='create_date, step', limit=2)
                                                            for zz in last_incr_amount:
                                                                print({'amount':zz.amount,
                                                                      'step':zz.step,

                                                                      })

                                                            # last_incr_amount_diff = last_incr_amount[1].amount - \
                                                            #                         last_incr_amount[0].amount
                                                            # net_last_incr_amount_diff = last_incr_amount[1].net_amount - \
                                                            #                         last_incr_amount[0].net_amount
                                                            #
                                                            # print('last_incr_amount_diff', last_incr_amount_diff)

                                                            # print((job_step.step))
                                                            if job_step.step.isnumeric():
                                                                if int(job_step.step) <= int(job_step.scale_type_of_increase.max_step_for_increase):
                                                                    increase_amount = job_step.scale_type_of_increase.total_amount
                                                                    increase_net_amount = job_step.scale_type_of_increase.total_amount
                                                                    step_amount += increase_amount
                                                                    step_net_amount += increase_net_amount
                                                                    last_step_amount = step_amount
                                                                    last_net_amount = step_net_amount
                                                                    gss_step_amount = step_amount
                                                                    gss_step_net_amount = step_net_amount
                                                                else:
                                                                    # increase_amount = job_step.scale_type_of_increase.in_number
                                                                    # increase_net_amount = job_step.scale_type_of_increase.in_number
                                                                    step_amount = gss_step_amount + last_incr_amount_diff
                                                                    step_net_amount = gss_step_net_amount + net_last_incr_amount_diff

                                                            else:
                                                                # print('sssssssssssssssssssssssss')
                                                                if int(letter_to_number(job_step.step)) <= int(job_step.scale_type_of_increase.max_step_for_increase):
                                                                    increase_amount = job_step.scale_type_of_increase.total_amount
                                                                    increase_net_amount = job_step.scale_type_of_increase.total_amount
                                                                    step_amount += increase_amount
                                                                    step_net_amount += increase_net_amount
                                                                    last_step_amount = step_amount
                                                                    last_net_amount = step_net_amount
                                                                    gss_step_amount = step_amount
                                                                    gss_step_net_amount = step_net_amount

                                                                else:

                                                                    # print('step_amount',step_amount)
                                                                    # print('ddddddddddddddddddddddddddddddddd')
                                                                    # increase_amount = job_step.scale_type_of_increase.in_number
                                                                    # increase_net_amount = job_step.scale_type_of_increase.in_number
                                                                    step_amount = gss_step_amount + last_incr_amount_diff
                                                                    step_net_amount = gss_step_net_amount + net_last_incr_amount_diff
                                                                    # print('step_amount',step_amount)


                                                        else:
                                                            if job_step.step.isnumeric():

                                                                    increase_amount = job_step.scale_type_of_increase.total_amount
                                                                    increase_net_amount = job_step.scale_type_of_increase.total_amount
                                                                    step_amount += increase_amount
                                                                    step_net_amount += increase_net_amount
                                                            else:
                                                                    increase_amount = job_step.scale_type_of_increase.total_amount
                                                                    increase_net_amount = job_step.scale_type_of_increase.total_amount
                                                                    step_amount += increase_amount
                                                                    step_net_amount += increase_net_amount
                                                    self.env['salary.steps'].with_context(force_create=True).create({
                                                        'step': job_step.step,
                                                        'scale_id': job_step.scale_id.id or False,
                                                        'scale_type_of_increase': job_step.scale_type_of_increase.id or False,
                                                        'year': current_year,
                                                        'amount': step_amount,
                                                        'net_amount': step_net_amount,
                                                        'placement_id': job_step.placement_id and job_step.placement_id.id or False,
                                                        'last_placement_increase_amount':last_incr_amount_diff,
                                                        'last_placement_increase_net_amount':net_last_incr_amount_diff
                                                    })
                                    raise ValidationError('Job step 3')

                    return {
                        'name': ("Salary Scale"),
                        'type': 'ir.actions.act_window',
                        'res_model': 'salary.scale',
                        'view_mode': 'form',
                        'res_id': new_salary_scale_id.id,
                    }

    def _calculate_step_values(self, count, salary_scale_id):
        if salary_scale_id.step_name_type == 'number':
            count += 1
            step_val = count
        elif salary_scale_id.step_name_type == 'alphabet':
            if count == 1:
                step_val = 'A'
            else:
                step_val = chr(ord('A') + (count - 1))
            count += 1
        return step_val, count

    def _calculate_increase_and_tax(self, step, step_amount, res, salary_scale_id, step_net_amount):
        increase_amount = 0
        if salary_scale_id.type_of_increase == 'ratio':
            if res.scale_type_of_increase.max_step_for_increase:
                if step < int(res.scale_type_of_increase.max_step_for_increase):
                    increase_amount = step_amount * (salary_scale_id.in_ratio / 100)
                    tax = self.compute_tax_amount(step_amount)
                    step_amount += increase_amount
            else:
                increase_amount = step_amount * (salary_scale_id.in_ratio / 100)
                tax = self.compute_tax_amount(step_amount)
                step_amount += increase_amount
        elif salary_scale_id.type_of_increase == 'number':
            if res.scale_type_of_increase.max_step_for_increase:
                if step < int(res.scale_type_of_increase.max_step_for_increase):
                    increase_amount = salary_scale_id.in_number
                    tax = self.compute_tax_amount(step_amount)
                    step_amount += increase_amount
            else:
                increase_amount = salary_scale_id.in_number
                tax = self.compute_tax_amount(step_amount)
                step_amount += increase_amount

        if salary_scale_id.currency_id.name == 'USD':
            step_net_amount += increase_amount
        elif salary_scale_id.currency_id.name == 'EGP':
            step_amount += increase_amount

        return step_amount, tax, step_net_amount

    def _create_step_record(self, step_val, res, tax, step_amount, step_net_amount):
        step_id = self.with_context(force_create=True).create({
            'step': step_val,
            'scale_id': res.scale_id.id or False,
            'scale_type_of_increase': res.scale_type_of_increase.id or False,
            'year': res.scale_id.year,
            'gss_placement_id': res.gss_placement_id.id or False,
            'tax_amount': tax,
            'amount': step_amount,
            'net_amount': step_net_amount,
            'job_id': res.job_id.id or False
        })
        return step_id

    def button_salary_scale_creation(self, args):
        res = args[0]
        salary_scale_id = args[1]
        step_amount = args[2]
        step_net_amount = args[3]
        count = 1
        val = 'A'

        for step in range(1, salary_scale_id.no_of_steps):
            step_val, count = self._calculate_step_values(count, salary_scale_id)
            step_amount, tax, step_net_amount = self._calculate_increase_and_tax(step, step_amount, res, salary_scale_id, step_net_amount)
            step_id = self._create_step_record(step_val, res, tax, step_amount, step_net_amount)

        return True