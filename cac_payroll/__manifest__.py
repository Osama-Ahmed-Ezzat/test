# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Salary Calculation Extension",
    "version": "15.0.0.2",
    "depends": ['base','hr',],
    "author": "Pragmatic Techsoft Pvt. Ltd.",
    "category": "hr",
    "summary": "Yearly Auto Increment In Salary",
    'license': 'OPL-1',
    "description": """
    To Calculate Salary Based on Some Conditions
""",
    'website': 'http://www.pragtech.co.in',
    'init_xml': [],
    'data': [
        'data/cron_job.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/salary_scale_wiz_view.xml',
        'views/general_ratio_view.xml',
        'views/salary_scale_view.xml',
        'views/employee_job_view.xml',
        'views/job_position_view.xml',
        'views/salary_step_view.xml',
        'views/placment.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': True,
}
