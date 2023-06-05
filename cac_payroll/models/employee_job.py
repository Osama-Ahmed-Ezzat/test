# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class EmployeeJob(models.Model):
    _name = 'employee.job'
    _description = "Employee Job"

    name = fields.Char("Name")
    scale_id = fields.Many2one('salary.scale',"Scale")
    step_ids = fields.One2many('salary.steps','job_id',"Steps")
    
    # Onchange Function To Auto Generate Steps
    @api.onchange('scale_id')
    def _onchange_scale_id(self):
        for rec in self:
            rec.step_ids = False
            if rec.scale_id and rec.scale_id.no_of_steps>0:
                steps=rec.scale_id.no_of_steps
                if rec.scale_id.step_name_type == 'number':
                    for i in range(steps):
                        self.env['salary.steps'].create({
                            'step':i+1,
                            'job_id': rec.id,
                        })
                elif rec.scale_id.step_name_type == 'alphabet':
                    val = 'A'
                    for i in range(steps):
                        self.env['salary.steps'].create({
                            'step':val,
                            'job_id': rec.id,
                        })
                        val=chr(ord(val) + 1)
    
    # Constrains To Avoid Duplication
    @api.constrains("scale_id")
    def check_scale_id(self):
        for rec in self:
            all_record_ids = self.search([('id','!=',self.id)])
            if all_record_ids:
                for record in all_record_ids:
                    if record.scale_id == self.scale_id:
                        raise ValidationError(_('You Can Not Create Multiple General Ratio Record In Same Year!!'))             

