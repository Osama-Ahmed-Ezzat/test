# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class GeneralRatio(models.Model):
    _name = 'general.ratio'
    _description = "General Ratio"
    _rec_name = 'year'
    
    
    year = fields.Char("Year")
    annual_increase_ratio = fields.Float("Annual Increase Ratio",default='6.5')
    cost_of_living = fields.Float("Cost Of Living")
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')],string="State",default='draft')
    
    #Approve Button Function 
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
    
    # Constrains To Avoid Duplication 
    @api.constrains("year")
    def check_year(self):
        for rec in self:
            lst = rec.year.split("/")
            if len(lst) == 1:
                raise ValidationError("Year should be in format '2021/2022'")
            all_record_ids = self.search([('id','!=',self.id)])
            if all_record_ids:
                for record in all_record_ids:
                    if record.year == self.year:
                        raise ValidationError(_('You Can Not Create Multiple General Ratio Record In Same Year!!'))