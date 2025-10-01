# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Spanish Localization Team
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
#from .hooks import post_init_hook
from . import models
#from . import wizard
#from . import controllers
from odoo import api, SUPERUSER_ID
#def pre_init_hook(cr, registry):
#    cr.execute('CREATE TABLE temp_universities (name VARCHAR(255);INSERT INTO temp_universities select distinct university_from from res_partner;
#               ALTER TABLE op_student'
#               'ADD COLUMN x_univer_backup character varying;')
#    cr.execute('INSERT INTO op_student '
#               'SET x_univer_backup valuesselect;')
    # in the installation the column phone is dropped

def post_init_hook(cr, registry):
#    env = api.Environment(cr, SUPERUSER_ID, {})
 #   result = self.env['res.partner'].read_group([ ("university", "!=", False) ], fields=['university'], groupby=['university'])
    #partners = env['res.partner'].search([])
    cr.execute("""INSERT INTO op_university (name) select distinct university from res_partner where university is not null;
               update res_partner rp set university_id=
               (select id from op_university where name=rp.university limit 1) 
               where university is not null;
               """)
    cr.execute("""INSERT INTO op_study_type (name) select distinct titulacion from res_partner where titulacion is not null;
               update res_partner rp set study_type_id=
               (select id from op_study_type where name=rp.titulacion limit 1) 
               where titulacion is not null;
               """)
    cr.execute("""INSERT INTO op_profession (name) select distinct profession from res_partner where profession is not null;
                update res_partner rp set profession_id=
                (select id from op_profession where name=rp.profession limit 1) 
                where profession is not null;
                """)
