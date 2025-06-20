# -*- coding: utf-8 -*-
# relative imports
import json
import logging
import datetime
import re
# absolute imports
from odoo import http
from odoo.http import request, Response
from itertools import groupby
from odoo.tools import date_utils
from odoo.addons.looker_connector.controllers.validate_token import validate_token

from math import ceil
import psycopg2
from urllib.parse import quote

_logger = logging.getLogger(__name__)


class LookerConnector(http.Controller):
    ''' Contain all the API's where You can get schema of tables and  getting the specified table data.'''
    @validate_token
    @http.route('/looker/query/data/', type='http', auth="none", methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def fetch_data(self, **kwargs):

        sql = kwargs['query']
        _logger.info(f"query {sql}")

        # sql='select * from res_users'

        cursor = request.env.cr
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # return str(schema)

        cursor.execute(sql)
        data = cursor.dictfetchall()
        print(len(data))

        params = {
            "count": int(kwargs.get('count', 20000)),
            "prev": None,
            "current": int(kwargs.get('current', 1)),
            "next": None,
            "total_pages": None,
            "data": [],
            "size": len(data)
        }
        size = len(data)
        params['total_pages'] = ceil(size / params.get('count'))

        params['next'] = None if params.get('current') == params.get(
            'total_pages') or params.get(
            'total_pages') == 0 else base_url + '/looker/query/data/' + '?query=' + quote(sql) + '&current=' + str(
            params.get('current') + 1)
        params['prev'] = None if params.get(
            'current') == 1 else base_url + '/looker/query/data/' + '?query=' + quote(sql) + '&current=' + str(
            params.get('current') - 1)
        if not params.get('prev', False):
            params.pop('prev')
        if not params.get('next', False):
            params.pop('next')

        to = params.get('current') * params.get('count')
        frm = to - params.get('count')

        if not params.get('total_pages', False):
            params.pop('current')
        try:
            with http.request.env.cr.savepoint():

                values = request.env.cr.execute(f'''
                                                                       {sql}
                                                                        LIMIT {params.get('count')} OFFSET {frm} '''
                                                )

                values = request.env.cr.dictfetchall()

                for item in values:
                    for key, value in item.items():
                        if isinstance(value, datetime.datetime):
                            item[key] = value.strftime("%Y%m%d%H%M%S")
                        elif isinstance(value, datetime.date):
                            item[key] = value.strftime("%Y%m%d")
                params['data'] = values

        except Exception as e:
            print("except")
            _logger.error(str(e))
            params['data'] = []
            status = 200

        return Response(json.dumps(params, default=date_utils.json_default), content_type='application/json')


    # @validate_token
    @http.route('/looker/query/check/', type='http', auth="none", methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def cehck(self, **kwargs):
        response = Response(json.dumps(
            {
                'data': [],
            },
        ),
            content_type='application/json',
            status=200
        )
        response.status = '200'
        return response


    @validate_token
    @http.route('/looker/', type='http', auth="none", methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def fetch_data_and_schema(self, **kwargs):
        sql = kwargs['query']

        _logger.info(f"query {sql}")
        cursor = request.env.cr

        with cursor:
            cursor.execute(sql)

            column_names = [desc[0] for desc in cursor.description]  # Extract column names
            column_types = [desc[1] for desc in cursor.description]

        schema = {name: type_ for name, type_ in zip(column_names, column_types)}

        response = Response(json.dumps(
            {
                'data': [],
                'schema': schema,
            },
            default=date_utils.json_default
        ),
            content_type='application/json',
            status=200
        )
        response.status = '200'
        return response


