# -*- coding: utf-8 -*-

from .import controllers
from .import models 
from odoo import api ,SUPERUSER_ID 
def bi_post_init_hook (OO0000OOOO00000OO ,O000O0000O0O00OO0 ):
    O0O000OO0OOO00OO0 =api .Environment (OO0000OOOO00000OO ,SUPERUSER_ID ,{})
    O0O000OO0OOO00OO0 ['ir.config_parameter'].set_param ('looker_connector.looker_access_token','*'*40 )
def bi_uninstall_hook (OOO0O0O00O0O00000 ,O0O00O0OOO0OOOO0O ):
    OO0OOOO0O0000O00O =api .Environment (OOO0O0O00O0O00000 ,SUPERUSER_ID ,{})
    OO0OOOO0O0000O00O ['ir.config_parameter'].set_param ('looker_connector.looker_access_token','*'*40 )
