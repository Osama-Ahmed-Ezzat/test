# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
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

class JobCategory(models.Model):
    _name = 'hr.job.category'

    name = fields.Char()


class JobPosition(models.Model):
    _inherit = 'hr.job'

    category_id = fields.Many2one('hr.job.category', "Category")
    scale_id = fields.Many2one('salary.scale', "Scale")
    step_ids = fields.One2many('salary.steps', 'job_id', "Steps")
    year = fields.Char("Year")
    is_usd = fields.Boolean(compute='_compute_is_usd', store=True)

    # Onchange Function To Auto Generate Steps
    @api.onchange('scale_id')
    def _onchange_scale_id(self):
        for rec in self:
            rec.step_ids = False

            if rec.scale_id and rec.scale_id.no_of_steps > 0:
                rec.year = rec.scale_id.year or ''
                steps = rec.scale_id.no_of_steps
                if rec.scale_id.step_name_type == 'number':
                    for i in range(steps):
                        self.env['salary.steps'].create({
                            'step': i + 1,
                            'job_id': rec.id,
                        })
                elif rec.scale_id.step_name_type == 'alphabet':
                    val = 'A'
                    for i in range(steps):
                        self.env['salary.steps'].create({
                            'step': val,
                            'job_id': rec.id,
                        })
                        val = chr(ord(val) + 1)

    @api.depends('step_ids', 'step_ids.currency_id')
    def _compute_is_usd(self):
        for rec in self:
            if rec.step_ids and rec.step_ids[0].currency_id and rec.step_ids[0].currency_id.symbol == '$':
                rec.is_usd = True
            else:
                rec.is_usd = False


class SalarySteps(models.Model):
    _name = 'salary.steps'
    _description = "Employee Steps"
    _rec_name = 'year'
    def get_gss_placement_domain(self):
        list_gss = []

        for rec in self.env['salary.steps'].search([]):
            if rec.scale_id.is_gss_scale == True:
                if rec.placement_id.id not in list_gss:
                    list_gss.append(rec.placement_id.id)
        print(list_gss)
        return [('id','in',list_gss)]

    step = fields.Char(string="Steps")
    currency_id = fields.Many2one(comodel_name='res.currency', related='scale_id.currency_id')
    amount = fields.Monetary("Gross Salary", currency_field='currency_id')
    net_amount = fields.Monetary("Net Salary", currency_field='currency_id')
    tax_amount = fields.Float(string="Tax Amount", required=False)
    job_id = fields.Many2one('hr.job', "Job Position")
    placement_id = fields.Many2one('salary.steps.placement', "Salary Step Placement")
    category_id = fields.Many2one(string="Job Category", related="job_id.category_id", store=True)
    scale_id = fields.Many2one('salary.scale', "Salary Scale")
    year = fields.Char('Year')
    active = fields.Boolean(default=True)
    scale_type_of_increase = fields.Many2one('salary.scale.typeof.increase', 'Type Of Increase',store=True,readonly=False,compute="compute_gss_placment_ratio")
    step_increase_amount = fields.Float('Increase Amount', compute='compute_increase_amount',store=True)
    gss_placement_id = fields.Many2one('salary.steps.placement','Gss Placement',domain=get_gss_placement_domain)
    last_placement_increase_amount = fields.Float()
    last_placement_increase_net_amount = fields.Float()
    @api.depends('gss_placement_id')
    def compute_gss_placment_ratio(self):
        for rec in self:
            if rec.gss_placement_id:
                gss_plac = self.env['salary.steps'].search([('placement_id','=',rec.gss_placement_id.id)],limit=1)
                if gss_plac.scale_type_of_increase:
                    rec.scale_type_of_increase = gss_plac.scale_type_of_increase.id
    @api.depends('placement_id', 'amount', 'scale_id', 'net_amount')
    def compute_increase_amount(self):
        cr = self._cr
        query = """SELECT id,step,
                       scale_id,
                       year,
                       net_amount,
                       amount,
                       placement_id,
                       amount - LAG(amount)
                                OVER (PARTITION by placement_id ORDER BY id ) AS increase_amount


                from salary_steps
                where placement_id is not null
                ORDER BY id , placement_id;
        """
        cr.execute(query)
        dat = cr.dictfetchall()

        # steps = self.env['salary.steps'].search([])
        for rec in self:
            for item in dat:
                if item['id'] == rec.id:

                    rec.step_increase_amount = item['increase_amount']

    # def _get_tax_slices(self, amount):
    #     slice_1 = slice_2 = slice_3 = slice_4 = slice_5, slice_6 = slice_7 = 0.0
    #     if amount > 1250:
    #         slice_1 = 0
    #     elif

    def compute_tax_amount(self, amount):
        tax_rule_ids = self.env['salary.tax.rule'].search([])
        tot_amount = amount * 12
        total_tax = 0.0
        total_discount = 0.0
        if tot_amount:
            if self.env.user.company_id.payslip_tax_minimum_salary == 0:
                raise ValidationError(_("Please set Payslip Tax Minimum Salary"))
            if self.env.user.company_id.payslip_tax_minimum_salary_force == 0:
                raise ValidationError(_("Please set Payslip Tax Minimum Force"))
            tot_amount = tot_amount - self.env.user.company_id.payslip_tax_minimum_salary
            if tot_amount <= self.env.user.company_id.payslip_tax_minimum_salary_force:
                for line in tax_rule_ids:
                    if not line.level == str(len(tax_rule_ids)):
                        if tot_amount > (line.amount_to - line.amount_from):
                            total_tax += line.total_tax
                            tot_amount -= (line.amount_to - line.amount_from)

                        elif tot_amount <= (line.amount_to - line.amount_from):
                            tax_level = tot_amount * (line.tax_rate / 100)
                            total_tax += tax_level
                            total_discount = total_tax * (line.tax_exemption / 100)
                            break
                        else:
                            if tot_amount < line.amount_from:
                                tax_level = tot_amount * (line.tax_rate / 100)
                                total_tax += tax_level
                                total_discount = total_tax * (line.tax_exemption / 100)
                                break
                    else:
                        tax_level = tot_amount * (line.tax_rate / 100)
                        total_tax += tax_level
                        total_discount = total_tax * (line.tax_exemption / 100)
                        break
            else:
                for line in tax_rule_ids:
                    if line.force_amount_to > tot_amount > line.force_amount_from:
                        total_tax = tot_amount * (line.tax_rate / 100)
                        total_discount = total_tax * (line.tax_exemption / 100)
        tax_amount = total_tax - total_discount
        taxes = self.env['res.config.settings'].search([])
        if taxes:
            for tax in taxes[-1]:
                if tax.payslip_tax_type == 'month':
                    return round(tax_amount / 12)
                    # payslip.write({'tax_amount': round(tax_amount / 12), 'payslip_tax_type': 'month'})
                else:
                    return round(tax_amount)
                    # payslip.write({'tax_amount': round(tax_amount), 'payslip_tax_type': 'annual'})
        else:
            return round(tax_amount / 12)
            # payslip.write({'tax_amount': round(tax_amount / 12), 'payslip_tax_type': 'month'})

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, '%s' % (record.step)))
        return result

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += [("step", operator, name)]
        return self.search(domain, limit=limit).name_get()

    @api.onchange('scale_id')
    def _onchange_scale_id(self):
        for rec in self:
            rec.year = rec.scale_id.year

    @api.model
    def create(self, values):
        res = super(SalarySteps, self).create(values)
        gss_step_amount = 0
        gss_step_net_amount = 0
        salary_scale_id = False
        if 'job_id' in values:
            raise ValidationError('000000000000000000000000000000000000000000000000000')

            job_id = self.env['hr.job'].browse(int(values['job_id']))
            if 'scale_id' in values:
                salary_scale_id = self.env['salary.scale'].browse(int(values['scale_id']))

            job_id = self.env['hr.job'].browse(int(values['job_id']))
            job_id.scale_id = salary_scale_id and salary_scale_id.id or False
            count = 0
            step_amount = 0
            step_net_amount = 0
            if salary_scale_id.step_name_type == 'number':
                counts = salary_scale_id.number_digits
            elif salary_scale_id.step_name_type == 'alphabet':
                counts = 1
            force_create = self.env.context.get('force_create')
            if job_id.step_ids and not force_create:
                for step in job_id.step_ids:
                    if step.scale_id == salary_scale_id:
                        count += 1
                if count > salary_scale_id.no_of_steps:
                    raise ValidationError(
                        _('No.of Steps Exceeded The Limit. You Can Not Add More Than One Steps Which Have Same Salary Scale!!'))
                step_amount = values['amount']
                if salary_scale_id.step_name_type == 'number':
                    res.step = counts
                elif salary_scale_id.step_name_type == 'alphabet':
                    val = 'A'
                    if count == 1:
                        res.step = val
                    else:
                        val = chr(ord(val) + (count - 1))
                        res.step = val
                for step in range(1, salary_scale_id.no_of_steps):
                    raise ValidationError('11111111111111111111111111111111111111')
                    if not salary_scale_id.is_gss_scale:
                        if salary_scale_id.type_of_increase == 'ratio':
                            increase_amount = step_amount * (salary_scale_id.in_ratio / 100)
                            tax = self.compute_tax_amount(step_amount)
                            step_amount += increase_amount
                        elif salary_scale_id.type_of_increase == 'number':
                            increase_amount = salary_scale_id.in_number
                            tax = self.compute_tax_amount(step_amount)
                            step_amount += increase_amount
                        if salary_scale_id.step_name_type == 'number':
                            counts += count
                            step_val = counts

                        elif salary_scale_id.step_name_type == 'alphabet':
                            val = 'A'

                            if count == 0:
                                step_val = val
                            else:
                                val = chr(ord(val) + (count))
                                count += 1
                                step_val = val
                        step_id = self.with_context(force_create=True).create({
                            'step': step_val,
                            'scale_id': salary_scale_id and salary_scale_id.id or False,
                            'year': res.scale_id.year,
                            'tax_amount': tax,
                            'amount': step_amount,
                            'job_id': res.job_id and res.job_id.id or False
                        })
                    else:
                        raise ValidationError('22222222222222222222222222222222222222222222')

                        if not res.gss_placement_id:
                            raise ValidationError('3333333333333333333333333333333333333333')

                            if salary_scale_id.type_of_increase == 'ratio':
                                increase_amount = step_amount * (res.scale_type_of_increase.in_ratio / 100)
                                tax = self.compute_tax_amount(step_amount)
                                step_amount += increase_amount
                            elif salary_scale_id.type_of_increase == 'number':

                                increase_amount = res.scale_type_of_increase.total_amount
                                tax = self.compute_tax_amount(step_amount)
                                step_amount += increase_amount
                            if salary_scale_id.step_name_type == 'number':
                                counts += count
                                step_val = counts

                            elif salary_scale_id.step_name_type == 'alphabet':
                                val = 'A'

                                if count == 0:
                                    step_val = val
                                else:
                                    val = chr(ord(val) + (count))
                                    count += 1
                                    step_val = val
                            step_id = self.with_context(force_create=True).create({
                                'step': step_val,
                                'scale_id': salary_scale_id and salary_scale_id.id or False,
                                'scale_type_of_increase': res.scale_type_of_increase and res.scale_type_of_increase.id or False,
                                'year': res.scale_id.year,
                                'tax_amount': tax,
                                'amount': step_amount,
                                'job_id': res.job_id and res.job_id.id or False
                            })
                        else:
                            raise ValidationError('44444444444444444444444444444444444444444444444')

                            if salary_scale_id.type_of_increase == 'ratio':
                                increase_amount = step_amount * (res.scale_type_of_increase.in_ratio / 100)
                                gss_increase_amount = increase_amount * (
                                        res.scale_type_of_increase.senior_rate / 100)
                                increase_amount = gss_increase_amount + increase_amount
                                tax = self.compute_tax_amount(step_amount)
                                step_amount += increase_amount
                            elif salary_scale_id.type_of_increase == 'number':

                                increase_amount = res.scale_type_of_increase.total_amount
                                gss_increase_amount = increase_amount * (
                                        res.scale_type_of_increase.senior_rate / 100)
                                increase_amount = gss_increase_amount + increase_amount
                                tax = self.compute_tax_amount(step_amount)
                                step_amount += increase_amount
                            if salary_scale_id.step_name_type == 'number':
                                counts += count
                                step_val = counts

                            elif salary_scale_id.step_name_type == 'alphabet':
                                val = 'A'

                                if count == 0:
                                    step_val = val
                                else:
                                    val = chr(ord(val) + (count))
                                    count += 1
                                    step_val = val
                            step_id = self.with_context(force_create=True).create({
                                'step': step_val,
                                'scale_id': salary_scale_id and salary_scale_id.id or False,
                                'scale_type_of_increase': res.scale_type_of_increase and res.scale_type_of_increase.id or False,
                                'year': res.scale_id.year,
                                'gss_placement_id':res.gss_placement_id,
                                'tax_amount': tax,
                                'amount': step_amount,
                                'job_id': res.job_id and res.job_id.id or False
                            })
        elif 'placement_id' in values:
            # raise ValidationError('666666666666666666666666666666666666666666666666666666666666666')

            placement_id = self.env['salary.steps.placement'].browse(int(values['placement_id']))
            if 'scale_id' in values:
                salary_scale_id = self.env['salary.scale'].browse(int(values['scale_id']))

            placement_id = self.env['salary.steps.placement'].browse(int(values['placement_id']))
            placement_id.scale_id = salary_scale_id and salary_scale_id.id or False
            count = 0
            step_amount = 0
            step_net_amount = 0
            if salary_scale_id.step_name_type == 'number':
                counts = salary_scale_id.number_digits
            elif salary_scale_id.step_name_type == 'alphabet':
                counts = 1
            force_create = self.env.context.get('force_create')
            if placement_id.step_ids and not force_create:
                for step in placement_id.step_ids:
                    if step.scale_id == salary_scale_id:
                        count += 1
                if count > salary_scale_id.no_of_steps:
                    raise ValidationError(
                        _('No.of Steps Exceeded The Limit. You Can Not Add More Than One Steps Which Have Same Salary Scale!!'))
                step_amount = values['net_amount'] if salary_scale_id.currency_id.symbol == '$' else values['amount']

                if salary_scale_id.step_name_type == 'number':
                    res.step = counts
                elif salary_scale_id.step_name_type == 'alphabet':
                    val = 'A'
                    if count == 1:
                        res.step = val
                    else:
                        val = chr(ord(val) + (count - 1))
                        res.step = val
                for step in range(1, salary_scale_id.no_of_steps):
                    if not res.gss_placement_id:

                        if not salary_scale_id.is_gss_scale:

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

                            if salary_scale_id.step_name_type == 'number':
                                counts += count
                                step_val = counts

                            elif salary_scale_id.step_name_type == 'alphabet':
                                val = 'A'

                                if count == 0:
                                    step_val = val
                                else:
                                    val = chr(ord(val) + (count))
                                    count += 1
                                    step_val = val
                            print('step_amount',)
                            # raise ValidationError('99999999999999999999999999999999999')

                            step_record = {
                                'step': step_val,
                                'scale_id': salary_scale_id and salary_scale_id.id or False,
                                'year': res.scale_id.year,
                                'tax_amount': tax,
                                'placement_id': res.placement_id and res.placement_id.id or False
                            }

                            if salary_scale_id.currency_id.name == 'USD':
                                step_record['net_amount'] = step_amount
                            elif salary_scale_id.currency_id.name == 'EGP':
                                step_record['amount'] = step_amount
                            step_id = self.with_context(force_create=True).create(step_record)


                        else:
                            raise ValidationError('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

                            last_incr_amount = self.env['salary.steps'].search(
                                [('placement_id', '=', res.placement_id.id),
                                 ('scale_id', '=', res.scale_id.id)],
                                order='create_date, step', limit=2)
                            for zz in last_incr_amount:
                                print({'amount': zz.amount,
                                       'step': zz.step,

                                       })
                            # last_incr_amount_diff = last_incr_amount[1].amount - \
                            #                         last_incr_amount[0].amount
                            # net_last_incr_amount_diff = last_incr_amount[1].net_amount - \
                            #                             last_incr_amount[0].net_amount

                            if salary_scale_id.type_of_increase == 'ratio':
                                if res.scale_type_of_increase.max_step_for_increase:
                                        if step < int(res.scale_type_of_increase.max_step_for_increase):
                                            increase_amount = step_amount * (res.scale_type_of_increase.in_ratio / 100)
                                            tax = self.compute_tax_amount(step_amount)
                                            step_amount += increase_amount
                                        else:
                                            increase_amount = res.last_placement_increase_amount
                                            tax = self.compute_tax_amount(step_amount)
                                            step_amount += increase_amount
                                else:
                                    increase_amount = step_amount * (res.scale_type_of_increase.in_ratio / 100)
                                    tax = self.compute_tax_amount(step_amount)
                                    step_amount += increase_amount

                            elif salary_scale_id.type_of_increase == 'number':
                                print('last_placement_increase_amount',res.last_placement_increase_amount)

                                if res.scale_type_of_increase.max_step_for_increase:

                                        if step < int(res.scale_type_of_increase.max_step_for_increase):
                                            increase_amount = res.scale_type_of_increase.total_amount
                                            tax = self.compute_tax_amount(step_amount)
                                            step_amount += increase_amount
                                            print('increase_amount',increase_amount)
                                            print('step_amount',step_amount)
                                            gss_step_amount = step_amount

                                        else:
                                            increase_amount = res.last_placement_increase_amount
                                            tax = self.compute_tax_amount(step_amount)
                                            step_amount = gss_step_amount + increase_amount

                                else:
                                    increase_amount = res.scale_type_of_increase.total_amount
                                    tax = self.compute_tax_amount(step_amount)
                                    step_amount += increase_amount
                            if salary_scale_id.step_name_type == 'number':
                                counts += count
                                step_val = counts

                            elif salary_scale_id.step_name_type == 'alphabet':
                                val = 'A'

                                if count == 0:
                                    step_val = val
                                else:
                                    val = chr(ord(val) + (count))
                                    count += 1
                                    step_val = val
                            step_id = self.with_context(force_create=True).create({
                                'step': step_val,
                                'scale_id': salary_scale_id and salary_scale_id.id or False,
                                'scale_type_of_increase': res.scale_type_of_increase and res.scale_type_of_increase.id or False,

                                'year': res.scale_id.year,
                                'tax_amount': tax,
                                'amount': step_amount,
                                'placement_id': res.placement_id and res.placement_id.id or False
                            })
                    else:
                        raise ValidationError('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww')

                        if not salary_scale_id.is_gss_scale:
                            if salary_scale_id.type_of_increase == 'ratio':
                                if res.scale_type_of_increase.max_step_for_increase:
                                    if step < int(res.scale_type_of_increase.max_step_for_increase):


                                        increase_amount = step_amount * (salary_scale_id.in_ratio / 100)
                                        gss_increase_amount = increase_amount * (
                                                res.scale_type_of_increase.senior_rate / 100)
                                        increase_amount = gss_increase_amount + increase_amount
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
                                        gss_increase_amount = increase_amount * (
                                                res.scale_type_of_increase.senior_rate / 100)
                                        increase_amount = gss_increase_amount + increase_amount
                                        tax = self.compute_tax_amount(step_amount)
                                        step_amount += increase_amount
                                else:
                                    increase_amount = salary_scale_id.in_number
                                    tax = self.compute_tax_amount(step_amount)
                                    step_amount += increase_amount

                            if salary_scale_id.step_name_type == 'number':
                                counts += count
                                step_val = counts

                            elif salary_scale_id.step_name_type == 'alphabet':
                                val = 'A'

                                if count == 0:
                                    step_val = val
                                else:
                                    val = chr(ord(val) + (count))
                                    count += 1
                                    step_val = val
                            step_id = self.with_context(force_create=True).create({
                                'step': step_val,
                                'scale_id': salary_scale_id and salary_scale_id.id or False,
                                'year': res.scale_id.year,
                                'tax_amount': tax,
                                'amount': step_amount,
                                'gss_placement_id':res.gss_placement_id.id,
                                'placement_id': res.placement_id and res.placement_id.id or False
                            })
                        else:
                            last_incr_amount = self.env['salary.steps'].search(
                                [('placement_id', '=', res.placement_id.id),
                                 ('scale_id', '=', res.scale_id.id)],
                                order='create_date, step', limit=2)
                            for zz in last_incr_amount:
                                print({'amount': zz.amount,
                                       'step': zz.step,

                                       })
                            # last_incr_amount_diff = last_incr_amount[1].amount - \
                            #                         last_incr_amount[0].amount
                            # net_last_incr_amount_diff = last_incr_amount[1].net_amount - \
                            #                             last_incr_amount[0].net_amount

                            if salary_scale_id.type_of_increase == 'ratio':
                                if res.scale_type_of_increase.max_step_for_increase:
                                    if step < int(res.scale_type_of_increase.max_step_for_increase):

                                        increase_amount = step_amount * (res.scale_type_of_increase.in_ratio / 100)
                                        gss_increase_amount = increase_amount * (
                                                res.scale_type_of_increase.senior_rate / 100)
                                        increase_amount = gss_increase_amount + increase_amount
                                        tax = self.compute_tax_amount(step_amount)
                                        step_amount += increase_amount
                                        gss_step_amount = step_amount
                                    else:
                                        increase_amount = res.last_placement_increase_amount
                                        tax = self.compute_tax_amount(step_amount)
                                        step_amount = gss_step_amount + increase_amount

                                else:

                                    increase_amount = step_amount * (res.scale_type_of_increase.in_ratio / 100)
                                    gss_increase_amount = increase_amount * (
                                            res.scale_type_of_increase.senior_rate / 100)
                                    increase_amount = gss_increase_amount + increase_amount
                                    tax = self.compute_tax_amount(step_amount)
                                    step_amount += increase_amount

                            elif salary_scale_id.type_of_increase == 'number':

                                if res.scale_type_of_increase.max_step_for_increase:
                                        if step < int(res.scale_type_of_increase.max_step_for_increase):

                                            increase_amount = res.scale_type_of_increase.total_amount
                                            gss_increase_amount = increase_amount * (
                                                    res.scale_type_of_increase.senior_rate / 100)
                                            increase_amount = gss_increase_amount + increase_amount
                                            tax = self.compute_tax_amount(step_amount)
                                            step_amount += increase_amount
                                            gss_step_amount = step_amount

                                        else:
                                            gss_inc_amount = res.last_placement_increase_amount


                                            tax = self.compute_tax_amount(step_amount)
                                            step_amount = gss_step_amount + gss_inc_amount

                                else:


                                    increase_amount = res.scale_type_of_increase.total_amount
                                    gss_increase_amount = increase_amount * (
                                            res.scale_type_of_increase.senior_rate / 100)
                                    increase_amount = gss_increase_amount + increase_amount
                                    tax = self.compute_tax_amount(step_amount)
                                    step_amount += increase_amount
                            if salary_scale_id.step_name_type == 'number':
                                counts += count
                                step_val = counts

                            elif salary_scale_id.step_name_type == 'alphabet':
                                val = 'A'

                                if count == 0:
                                    step_val = val
                                else:
                                    val = chr(ord(val) + (count))
                                    count += 1
                                    step_val = val
                            step_id = self.with_context(force_create=True).create({
                                'step': step_val,
                                'scale_id': salary_scale_id and salary_scale_id.id or False,
                                'scale_type_of_increase': res.scale_type_of_increase and res.scale_type_of_increase.id or False,
                                'gss_placement_id':res.gss_placement_id.id,
                                'year': res.scale_id.year,
                                'tax_amount': tax,
                                'amount': step_amount,
                                'placement_id': res.placement_id and res.placement_id.id or False,
                                'last_placement_increase_amount':res.last_placement_increase_amount,
                                'last_placement_increase_net_amount':res.last_placement_increase_net_amount

                            })
        return res

    def write(self, values):
        res = super(SalarySteps, self).write(values)
        if 'scale_id' in values:
            count = 0
            if self.job_id.step_ids:
                for step in self.job_id.step_ids:
                    if step.scale_id == self.scale_id:
                        count += 1
                if count > self.scale_id.no_of_steps:
                    raise ValidationError(_('No.of Steps Exceeded The Limit!!'))
        elif 'scale_id' in values:
            count = 0
            if self.placement_id.step_ids:
                for step in self.placement_id.step_ids:
                    if step.scale_id == self.scale_id:
                        count += 1
                if count > self.scale_id.no_of_steps:
                    raise ValidationError(_('No.of Steps Exceeded The Limit!!'))

        return res


class ScaleReplacement(models.Model):
    _name = 'salary.steps.placement'
    # _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char(string="Placement", store=True)
    scale_id = fields.Many2one('salary.scale', "Scale")
    gss_placement = fields.Many2one('salary.steps.placement',compute='get_steps_gss_placement',store=True)
    typeof = fields.Many2one('salary.scale.typeof.increase',compute='get_steps_gss_placement',store=True)
    year = fields.Char(string="Year",compute='get_steps_gss_placement', store=True)
    step_ids = fields.One2many('salary.steps', 'placement_id', "Steps")
    is_usd = fields.Boolean(compute='_compute_is_usd', store=True)
    symbol = fields.Char(related='scale_id.currency_id.symbol')
    currency_id = fields.Many2one('res.currency', string='Currency',compute='get_steps_gss_placement',store=True)

    @api.depends('step_ids.gss_placement_id')
    def get_steps_gss_placement(self):
        for record in self:
            gss = False
            typeof = False
            currency = False
            year = ''
            for rec in record.step_ids:
                gss = rec.gss_placement_id.id
                typeof = rec.scale_type_of_increase.id
                currency = rec.currency_id.id
                year = rec.year
            record.gss_placement = gss
            record.typeof = typeof
            record.year = year
            record.currency_id = currency
    @api.onchange('scale_id')
    def _onchange_scale_id(self):
        for rec in self:
            rec.step_ids = False

            if rec.scale_id and rec.scale_id.no_of_steps > 0:
                rec.year = rec.scale_id.year or ''
                steps = rec.scale_id.no_of_steps
                if rec.scale_id.step_name_type == 'number':
                    for i in range(steps):
                        self.env['salary.steps'].create({
                            'step': i + 1,
                            'placement_id': rec.id,
                        })
                elif rec.scale_id.step_name_type == 'alphabet':
                    val = 'A'
                    for i in range(steps):
                        self.env['salary.steps'].create({
                            'step': val,
                            'placement_id': rec.id,
                        })
                        val = chr(ord(val) + 1)

    @api.depends('step_ids', 'step_ids.currency_id')
    def _compute_is_usd(self):
        for rec in self:
            if rec.step_ids and rec.step_ids[0].currency_id and rec.step_ids[0].currency_id.symbol == '$':
                rec.is_usd = True
            else:
                rec.is_usd = False
