# -*- coding: utf-8 -*-

import pytz
from datetime import datetime, timedelta, time
from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    irg_weekly_hours_total = fields.Float(
        string="Horas Semanales",
        compute="_compute_irg_weekly_hours_total",
        readonly=True,
        help="Total de horas trabajadas por el empleado durante la semana correspondiente a la fecha de entrada."
    )

    irg_monthly_hours_total = fields.Float(
        string="Horas Mensuales",
        compute="_compute_irg_monthly_hours_total",
        readonly=True,
        help="Total de horas trabajadas por el empleado durante el mes correspondiente a la fecha de entrada."
    )

    @api.depends('check_in', 'employee_id')
    def _compute_irg_weekly_hours_total(self):
        # Filtrar registros con check_in y employee_id definidos
        valid_records = self.filtered(lambda r: r.check_in and r.employee_id)
        
        # Inicializar a 0.0 los registros no válidos
        for record in (self - valid_records):
            record.irg_weekly_hours_total = 0.0

        if not valid_records:
            return

        # Diccionario para asociar cada registro con su clave de periodo único (employee_id, week_start, week_end)
        record_periods = {}
        for record in valid_records:
            # Obtener fecha en el huso horario del usuario
            local_dt = fields.Datetime.context_timestamp(record, record.check_in)
            local_date = local_dt.date()
            
            # Calcular lunes de esa semana
            week_start = local_date - timedelta(days=local_date.weekday())
            # Calcular domingo de esa semana
            week_end = week_start + timedelta(days=6)
            
            record_periods[record] = (record.employee_id.id, week_start, week_end)

        # Claves únicas de periodos a consultar para evitar N+1 queries
        unique_periods = set(record_periods.values())
        
        # Diccionario para almacenar los resultados del cálculo
        weekly_cache = {}
        
        # Obtener huso horario actual para la conversión exacta
        tz_name = self.env.context.get('tz') or self.env.user.tz or 'UTC'
        tz = pytz.timezone(tz_name)

        for employee_id, start_date, end_date in unique_periods:
            # Definir límites locales
            dt_start_local = tz.localize(datetime.combine(start_date, time.min))
            dt_end_local = tz.localize(datetime.combine(end_date, time.max))
            
            # Convertir límites locales a UTC para la consulta
            dt_start_utc = dt_start_local.astimezone(pytz.utc).replace(tzinfo=None)
            dt_end_utc = dt_end_local.astimezone(pytz.utc).replace(tzinfo=None)
            
            # Consultar sumatoria de worked_hours
            attendances_data = self.env['hr.attendance'].read_group(
                domain=[
                    ('employee_id', '=', employee_id),
                    ('check_in', '>=', dt_start_utc),
                    ('check_in', '<=', dt_end_utc)
                ],
                fields=['worked_hours:sum'],
                groupby=['employee_id']
            )
            
            total_hours = attendances_data[0]['worked_hours'] if attendances_data else 0.0
            weekly_cache[(employee_id, start_date, end_date)] = total_hours

        # Asignar los valores computados a los registros
        for record in valid_records:
            period_key = record_periods[record]
            record.irg_weekly_hours_total = weekly_cache.get(period_key, 0.0)

    @api.depends('check_in', 'employee_id')
    def _compute_irg_monthly_hours_total(self):
        # Filtrar registros con check_in y employee_id definidos
        valid_records = self.filtered(lambda r: r.check_in and r.employee_id)
        
        # Inicializar a 0.0 los registros no válidos
        for record in (self - valid_records):
            record.irg_monthly_hours_total = 0.0

        if not valid_records:
            return

        # Diccionario para asociar cada registro con su clave de periodo único (employee_id, month_start, month_end)
        record_periods = {}
        for record in valid_records:
            # Obtener fecha en el huso horario del usuario
            local_dt = fields.Datetime.context_timestamp(record, record.check_in)
            local_date = local_dt.date()
            
            # Calcular primer día del mes
            month_start = local_date.replace(day=1)
            # Calcular último día del mes
            if local_date.month == 12:
                month_end = local_date.replace(day=31)
            else:
                month_end = (local_date.replace(month=local_date.month + 1, day=1) - timedelta(days=1))
                
            record_periods[record] = (record.employee_id.id, month_start, month_end)

        # Claves únicas de periodos a consultar para evitar N+1 queries
        unique_periods = set(record_periods.values())
        
        # Diccionario para almacenar los resultados del cálculo
        monthly_cache = {}
        
        # Obtener huso horario actual para la conversión exacta
        tz_name = self.env.context.get('tz') or self.env.user.tz or 'UTC'
        tz = pytz.timezone(tz_name)

        for employee_id, start_date, end_date in unique_periods:
            # Definir límites locales
            dt_start_local = tz.localize(datetime.combine(start_date, time.min))
            dt_end_local = tz.localize(datetime.combine(end_date, time.max))
            
            # Convertir límites locales a UTC para la consulta
            dt_start_utc = dt_start_local.astimezone(pytz.utc).replace(tzinfo=None)
            dt_end_utc = dt_end_local.astimezone(pytz.utc).replace(tzinfo=None)
            
            # Consultar sumatoria de worked_hours
            attendances_data = self.env['hr.attendance'].read_group(
                domain=[
                    ('employee_id', '=', employee_id),
                    ('check_in', '>=', dt_start_utc),
                    ('check_in', '<=', dt_end_utc)
                ],
                fields=['worked_hours:sum'],
                groupby=['employee_id']
            )
            
            total_hours = attendances_data[0]['worked_hours'] if attendances_data else 0.0
            monthly_cache[(employee_id, start_date, end_date)] = total_hours

        # Asignar los valores computados a los registros
        for record in valid_records:
            period_key = record_periods[record]
            record.irg_monthly_hours_total = monthly_cache.get(period_key, 0.0)
