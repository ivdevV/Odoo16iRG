# -*- coding: utf-8 -*-

import json
import logging
import datetime
from odoo import http
from odoo.http import request, Response
from itertools import groupby
from odoo.tools import date_utils
from odoo.addons.looker_connector.controllers.validate_token import validate_token
from odoo.addons.looker_connector.common import datefields_extracter
from math import ceil

_O0OO0O0O00OO00000 = logging.getLogger(__name__)


class LookerConnector(http.Controller):
    @validate_token
    @http.route('/looker/schemas/', type='http', auth="none", methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_schema(OO0O00OOOO0O0OO00, **OOO0O0O00O0OO00OO):

        O0O0OOOOO0O00OO00 = lambda O00OO0OO00000O000: O00OO0OO00000O000['table_name']
        OOOO0000OOO0000O0 = dict()
        _O0OO0O0O00OO00000.info('getting database tables with its schema')
        try:
            with http.request.env.cr.savepoint():
                OOOO0OOO0O0O00OO0 = request.env.cr.execute(f'''
                                                    SELECT 
                                                    column_name,data_type AS column_type,table_name 
                                                    FROM 
                                                    information_schema.columns 
                                                    WHERE 
                                                    table_schema = 'public' 
                                                    ORDER BY table_name
                                                    ''')
                OOOO0OOO0O0O00OO0 = request.env.cr.dictfetchall()
                for O00OO00O00O0O00O0, O0000O0OO000OOO00 in groupby(OOOO0OOO0O0O00OO0, O0O0OOOOO0O00OO00):
                    O0000O0OO000OOO00 = list(O0000O0OO000OOO00)
                    OOOO0000OOO0000O0[O00OO00O00O0O00O0.replace('_', '.')] = [
                        {"column_name": OOO00OOOO0000OO00["column_name"],
                         "column_type": OOO00OOOO0000OO00["column_type"]} for OOO00OOOO0000OO00 in O0000O0OO000OOO00]
        except Exception as OO0000OO0OO0OOO00:
            _O0OO0O0O00OO00000.error(str(OO0000OO0OO0OOO00))
            return Response(json.dumps({'error': f'{str(OO0000OO0OO0OOO00)}'}, default=date_utils.json_default),
                            content_type='application/json', status=500)
        _O0OO0O0O00OO00000.info('Schema collection done')
        O0OO0OOO00OO00O00 = Response(json.dumps(OOOO0000OOO0000O0, default=date_utils.json_default),
                                     content_type='application/json', status=200)
        O0OO0OOO00OO00O00.status = '200'
        return O0OO0OOO00OO00O00

    @validate_token
    @http.route('/looker/tablenames/', type='http', auth="none", methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_model_names(O00OOOO0OOO0000O0, **O0O0OOO00000OOO00):

        _O0OO0O0O00OO00000.info('getting database tables')
        OOOOOOOOO0000OO00 = []
        try:
            with http.request.env.cr.savepoint():
                OO0OOOO00O0O0OO0O = request.env.cr.execute('''SELECT 
                                                    relname AS table  
                                                    FROM 
                                                    pg_stat_user_tables 
                                                    ORDER BY relname
                                                    ''')
                OO0OOOO00O0O0OO0O = request.env.cr.dictfetchall()
                for OO00OOOO0O0O0OOO0 in OO0OOOO00O0O0OO0O:
                    OOOOOOOOO0000OO00.append(OO00OOOO0O0O0OOO0['table'].replace('_', '.'))
        except Exception as O0O0O0000O00000OO:
            _O0OO0O0O00OO00000.error(str(O0O0O0000O00000OO))
            return Response(json.dumps({'error': f'{O0O0O0000O00000OO}'}, default=date_utils.json_default),
                            content_type='application/json', status=500)
        _O0OO0O0O00OO00000.info('tables collection done')
        return Response(json.dumps(OOOOOOOOO0000OO00, default=date_utils.json_default), content_type='application/json',
                        status=200)

    @validate_token
    @http.route('/looker/relationschema/', type='http', auth="none", methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_schema_relation(OO0OOO00O0O0OO0OO, **O0000OO0OO0O0OOO0):

        OO0OOO0OO0OOO0O00 = lambda O0O0O0OOO00O0O0OO: O0O0O0OOO00O0O0OO['table_name']
        O0O0O0O000OOO0O00 = dict()
        _O0OO0O0O00OO00000.info('getting database tables with its schema')
        try:
            with http.request.env.cr.savepoint():
                OO0OOOOOO0000O0O0 = request.env.cr.execute(f'''
                                                    SELECT 
                                                    column_name,data_type AS column_type,table_name 
                                                    FROM 
                                                    information_schema.columns 
                                                    WHERE 
                                                    table_schema = 'public' 
                                                    ORDER BY table_name
                                                    ''')
                OO0OOOOOO0000O0O0 = request.env.cr.dictfetchall()
                for OO0O0O00OOO00O0OO, OOOOOO00OO0OO0000 in groupby(OO0OOOOOO0000O0O0, OO0OOO0OO0OOO0O00):
                    OO0O0O00OOO00O0OO = OO0O0O00OOO00O0OO.replace('_', '.')
                    OOOOOO00OO0OO0000 = list(OOOOOO00OO0OO0000)
                    try:
                        OO0OO00OOOOOOOOOO = dict(request.env[OO0O0O00OOO00O0OO].sudo().fields_get())
                        for O0OOOO00O0O0O0O0O in OOOOOO00OO0OO0000:
                            try:
                                if "2" in str(OO0OO00OOOOOOOOOO[O0OOOO00O0O0O0O0O["column_name"]]["type"]):
                                    O0OOOO00O0O0O0O0O["column_type"] = \
                                    OO0OO00OOOOOOOOOO[O0OOOO00O0O0O0O0O["column_name"]]["type"]
                                    O0OOOO00O0O0O0O0O["column_relation"] = \
                                    OO0OO00OOOOOOOOOO[O0OOOO00O0O0O0O0O["column_name"]]["relation"]
                                else:
                                    O0OOOO00O0O0O0O0O["column_relation"] = "none"
                            except:
                                O0OOOO00O0O0O0O0O["column_relation"] = "none"
                    except:
                        pass
                    OO00O0O00000OO00O = list()
                    for O00OO0O0OOO0OOOO0 in OOOOOO00OO0OO0000:
                        try:
                            if O00OO0O0OOO0OOOO0["column_relation"]:
                                pass
                        except:
                            O00OO0O0OOO0OOOO0["column_relation"] = "none"
                        OO00O0O00000OO00O.append({"column_name": O00OO0O0OOO0OOOO0["column_name"],
                                                  "column_type": O00OO0O0OOO0OOOO0["column_type"],
                                                  "column_relation": O00OO0O0OOO0OOOO0["column_relation"]})
                        O0O0O0O000OOO0O00[OO0O0O00OOO00O0OO.replace('_', '.')] = OO00O0O00000OO00O
        except Exception as OOOO0000OO0O0O0O0:
            _O0OO0O0O00OO00000.error(str(OOOO0000OO0O0O0O0))
            return Response(json.dumps({'error': f'{str(OOOO0000OO0O0O0O0)}'}, default=date_utils.json_default),
                            content_type='application/json', status=500)
        _O0OO0O0O00OO00000.info('Schema collection done')
        OO00OOOO0000O00OO = Response(json.dumps(O0O0O0O000OOO0O00, default=date_utils.json_default),
                                     content_type='application/json', status=200)
        OO00OOOO0000O00OO.status = '200'
        return OO00OOOO0000O00OO

    @validate_token
    @http.route(['/looker/connector/<string:model>', '/looker/connector/<string:model>/'], type='http', auth="none",
                methods=['GET', 'OPTIONS'], website=True, csrf=False, cors='*')
    def get_modeldate(OO0O0OOO0OOOO000O, model, **OOO0000O0O00O0O00):

        _O0OO0O0O00OO00000.info(f'getting data of {model} ')
        O00000OOO00O00O00 = 200
        O00OOO000OOOO00OO = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        O0OO0O0O0O00O000O = False
        try:
            request.env.cr.execute(f'''
                                SELECT
                                COUNT(*) AS size
                                FROM
                                {model.replace('.', '_')}
                                ''')
            O0OO0O0O0O00O000O = request.env.cr.dictfetchall()[0]['size']
        except Exception as OO0O0O00O0OOO0000:
            _O0OO0O0O00OO00000.error(str(OO0O0O00O0OOO0000))
            OOOO0O0O000O0OOOO = {'error': str(OO0O0O00O0OOO0000)}
            O00000OOO00O00O00 = 500
            return Response(json.dumps(OOOO0O0O000O0OOOO, default=date_utils.json_default),
                            content_type='application/json', status=O00000OOO00O00O00)
        OOOO0O0O000O0OOOO = {"count": int(OOO0000O0O00O0O00.get('count', 20000)), "prev": None,
                             "current": int(OOO0000O0O00O0O00.get('current', 1)), "next": None, "total_pages": None,
                             "data": [], "size": O0OO0O0O0O00O000O}
        OOOO0O0O000O0OOOO['total_pages'] = ceil(O0OO0O0O0O00O000O / OOOO0O0O000O0OOOO.get('count'))
        OOOO0O0O000O0OOOO['next'] = None if OOOO0O0O000O0OOOO.get('current') == OOOO0O0O000O0OOOO.get(
            'total_pages') or OOOO0O0O000O0OOOO.get(
            'total_pages') == 0 else O00OOO000OOOO00OO + '/looker/connector/' + model + '?current=' + str(
            OOOO0O0O000O0OOOO.get('current') + 1)
        OOOO0O0O000O0OOOO['prev'] = None if OOOO0O0O000O0OOOO.get(
            'current') == 1 else O00OOO000OOOO00OO + '/looker/connector/' + model + '?current=' + str(
            OOOO0O0O000O0OOOO.get('current') - 1)
        if not OOOO0O0O000O0OOOO.get('prev', False):
            OOOO0O0O000O0OOOO.pop('prev')
        if not OOOO0O0O000O0OOOO.get('next', False):
            OOOO0O0O000O0OOOO.pop('next')
        O0OO0O00000O00O00 = OOOO0O0O000O0OOOO.get('current') * OOOO0O0O000O0OOOO.get('count')
        O0OOO00OOO00O000O = O0OO0O00000O00O00 - OOOO0O0O000O0OOOO.get('count')
        if not OOOO0O0O000O0OOOO.get('total_pages', False):
            OOOO0O0O000O0OOOO.pop('current')
        try:
            with http.request.env.cr.savepoint():
                O00O00O0OO0O00O0O = request.env.cr.execute(f'''
                                                SELECT *
                                                FROM
                                                {model.replace('.', '_')}
                                                LIMIT {OOOO0O0O000O0OOOO.get('count')} OFFSET {O0OOO00OOO00O000O} ''')
                records = request.env.cr.dictfetchall()
                O00O00O0OO0O00O0O = None
                O00O00O0OO0O00O0O = [dict(record) for record in records]
                
                        
                for O00O00O00OO0O0OOO in O00O00O0OO0O00O0O:
                    for OO0OO00O00O00000O, O00O000O0OOOO0O00 in O00O00O00OO0O0OOO.items():
                        if isinstance(O00O000O0OOOO0O00, datetime.datetime):
                            O00O00O00OO0O0OOO[OO0OO00O00O00000O] = O00O000O0OOOO0O00.strftime("%Y%m%d%H%M%S")
                        elif isinstance(O00O000O0OOOO0O00, datetime.date):
                            O00O00O00OO0O0OOO[OO0OO00O00O00000O] = O00O000O0OOOO0O00.strftime("%Y%m%d")
                            
                for O00O00O00OO0O0OOO in O00O00O0OO0O00O0O:
                    if model == 'crm.lead' or model == 'crm_lead':
                        O00O00O00OO0O0OOO['description'] = ""
                        
                OOOO0O0O000O0OOOO['data'] = O00O00O0OO0O00O0O

        except Exception as OO0O0O00O0OOO0000:
            print("except")
            _O0OO0O0O00OO00000.error(str(OO0O0O00O0OOO0000))
            OOOO0O0O000O0OOOO['data'] = []
            O00000OOO00O00O00 = 200
        return Response(json.dumps(OOOO0O0O000O0OOOO, default=date_utils.json_default), content_type='application/json',
                        status=O00000OOO00O00O00)
