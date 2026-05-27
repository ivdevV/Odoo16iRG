# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Override del onchange de irg_sale_order_extended para evitar que machaque el estudiante
    # si ya tiene un valor distinto, o simplemente para permitir que sean distintos.
    @api.onchange('partner_id')
    def _onchange_student_id(self):
        # Mantenemos la lógica de irg_sale_order_extended SOLO si el student_id está vacío
        # o si queremos forzar que por defecto sea el partner, PERO
        # permitiendo cambiarlo después sin que vuelva a cambiar automáticamente 
        # a menos que volvamos a cambiar el partner.
        if self.partner_id and not self.student_id:
            self.student_id = self.partner_id

    def _create_or_get_admission(self, line):
        _logger.warning("=" * 60)
        _logger.warning("ISEP_ADMISSION_FROM_STUDENT: _create_or_get_admission EJECUTADO")
        _logger.warning(f"Orden: {self.name}")
        _logger.warning(f"student_id: {self.student_id.name if self.student_id else 'VACIO'} (ID: {self.student_id.id if self.student_id else 'N/A'})")
        _logger.warning(f"partner_id: {self.partner_id.name if self.partner_id else 'VACIO'} (ID: {self.partner_id.id if self.partner_id else 'N/A'})")
        _logger.warning("=" * 60)
        
        try:
            _logger.warning("ISEP_DEBUG: Intentando construir dominio...")
            domain = ['|', 
                     ('product_template_id', '=', line.product_template_id.id),
                     ('product_template_ids', 'in', line.product_template_id.id)]
            
            _logger.warning(f"ISEP_DEBUG: Domain construido: {domain}")
            
            course = self.env['op.course'].search(domain, limit=1)
            _logger.warning(f"ISEP_DEBUG: Course found: {course}")
            
            if not course:
                self._upsert_admission_row(
                    line,
                    error_msg=f"No se encontró Curso para {line.product_template_id.display_name}.",
                )
                _logger.warning("ISEP_DEBUG: No course found. Returning False.")
                return False

            if not self.period:
                if not self.admission_date:
                    # Intentar obtener fecha de start_date (suscripciones) o date_order
                    if hasattr(self, 'start_date') and self.start_date:
                        self.admission_date = self.start_date
                    elif self.date_order:
                        self.admission_date = self.date_order.date()
                    else:
                        self.admission_date = fields.Date.today()
                    _logger.warning(f"ISEP_DEBUG: Forced admission_date to {self.admission_date}")

                self._compute_period()
            _logger.warning(f"ISEP_DEBUG: Period: {self.period}")

            if not self.period:
                self._upsert_admission_row(
                    line,
                    course=course,
                    error_msg="No se pudo determinar el Periodo de Admisión.",
                )
                _logger.warning("ISEP_DEBUG: No period found. Returning False.")
                return False

            register = self._find_or_create_register(
                period=self.period,
                product_template=line.product_template_id,
                course=course,
            )
            _logger.warning(f"ISEP_DEBUG: Register: {register}")

            admission = line.admission_id
            _logger.warning(f"ISEP_DEBUG: Existing admission on line: {admission}")
            
            # Fallback: Si no hay admisión en la línea, pero existe en la cabecera (creada manualmente), usémosla
            if not admission and self.admission_id:
                 _logger.warning(f"ISEP_DEBUG: Usando admisión existente en cabecera {self.admission_id.id}")
                 admission = self.admission_id
                 line.admission_id = admission.id

            # --- MODIFICACIÓN: Usar student_id (definido en irg_sale_order_extended) o partner_id ---
            target_partner = self.student_id or self.partner_id
            _logger.warning(f"ISEP_DEBUG: Target Partner: {target_partner.name} (ID: {target_partner.id})")
            
            # LOGICA DE ACTUALIZACIÓN (por si ya existía la admisión pero con partner incorrecto)
            if admission and admission.partner_id != target_partner:
                _logger.warning(f"ISEP_DEBUG: Actualizando admisión {admission.id} con nuevo partner {target_partner.name}")
                parts = (target_partner.name or '').split()
                first_name = ' '.join(parts[:-1]) if len(parts) > 1 else (parts[0] if parts else '-')
                last_name = parts[-1] if len(parts) > 1 else '-'
                
                admission.write({
                    'name': target_partner.name,
                    'first_name': (first_name or '-').strip(),
                    'last_name': (last_name or '-').strip(),
                    'email': target_partner.email,
                    'mobile': target_partner.mobile,
                    'phone': target_partner.phone,
                    'partner_id': target_partner.id,
                    'gender': self.gender or target_partner.gender or 'o',
                })

            if not admission:
                parts = (target_partner.name or '').split()
                first_name = ' '.join(parts[:-1]) if len(parts) > 1 else (parts[0] if parts else '-')
                last_name = parts[-1] if len(parts) > 1 else '-'

                # --- CORRECCIÓN ISEP: Asegurar student_id ---
                # Buscamos o creamos el op.student asociado al partner objetivo.
                # Esto es CRÍTICO para que search_user_portal en isep_openeducat_sale 
                # NO sobrescriba el partner_id con el del titular al ver que falta el student_id.
                op_student = self.env['op.student'].search([('partner_id', '=', target_partner.id)], limit=1)
                if not op_student:
                    _logger.warning(f"ISEP_DEBUG: Creando op.student para {target_partner.name} anticipadamente.")
                    target_user = self.env['res.users'].search([('partner_id', '=', target_partner.id)], limit=1)
                    
                    op_student = self.env['op.student'].create({
                         'name': target_partner.name,
                         'first_name': (first_name or '-').strip(),
                         'last_name': (last_name or '-').strip(),
                         'gender': self.gender or target_partner.gender or 'o',
                         'partner_id': target_partner.id,
                         'user_id': target_user.id if target_user else False,
                         'email': target_partner.email,
                         'mobile': target_partner.mobile,
                         'phone': target_partner.phone,
                         'birth_date': fields.Date.today(), # Valor por defecto requerido
                    })
                
                _logger.warning(f"ISEP_DEBUG: Creando Admisión con op.student {op_student.id} y partner {target_partner.id}.")

                admission = self.env['op.admission'].create({
                    'name': target_partner.name,
                    'first_name': (first_name or '-').strip(),
                    'last_name': (last_name or '-').strip(),
                    'sale_id': self.id,
                    'email': target_partner.email,
                    'mobile': target_partner.mobile,
                    'phone': target_partner.phone,
                    'partner_id': target_partner.id,
                    
                    # Campos añadidos para evitar sobrescritura incorrecta:
                    'student_id': op_student.id,
                    'is_student': True,
                    
                    'register_id': register.id,
                    'course_id': register.course_id.id,
                    'application_date': fields.Datetime.now(),
                    'admission_date': line.start_date_enroller or fields.Date.today(),
                    'fees_term_id': self.env['op.fees.terms'].search([], limit=1).id,
                    'gender': self.gender or target_partner.gender or 'o',
                    'batch_id': self.get_lot_id(course).id,
                    'order_id': self.id,
                })
                
                # --- VERIFICACIÓN Y CORRECCIÓN POST-CREATION ---
                # Si search_user_portal en isep_openeducat_sale sobrescribió la admisión
                # (devuelve al partner_id del pedido), lo arreglamos aquí.
                if admission.partner_id != target_partner:
                    _logger.warning(f"ISEP_DEBUG: Admisión {admission.id} fue sobrescrita durante create! Restaurando.")
                    _logger.warning(f"Valor incorrecto: {admission.partner_id.name} | Valor correcto: {target_partner.name}")
                    admission.write({
                        'partner_id': target_partner.id,
                        'student_id': op_student.id,
                        'is_student': True,
                        'mobile': target_partner.mobile,
                        'phone': target_partner.phone,
                        'email': target_partner.email,
                    })

                line.admission_id = admission.id

            return admission
        except Exception as e:
            _logger.error("ISEP_CRITICAL_ERROR: Exception in _create_or_get_admission", exc_info=True)
            raise e


    def create_admission_manual(self, admission_register_id):
        _logger.info(f"ISEP_DEBUG: create_admission_manual para orden {self.name}")
        _logger.info(f"ISEP_DEBUG: student_id={self.student_id}, partner_id={self.partner_id}")

        # Override para usar student_id en creación manual
        op_admission = self.env['op.admission']
        
        # --- MODIFICACIÓN: Usar student_id ---
        target_partner = self.student_id or self.partner_id
        _logger.info(f"ISEP_DEBUG: target_partner seleccionado: {target_partner.name} (ID: {target_partner.id})")

        name = target_partner.name.replace('  ',' ').replace('   ',' ').replace('    ',' ').replace('     ',' ').replace('      ',' ').split(' ')
        
        first_name = '-'
        last_name = '-'
        if len(name)==1:
            first_name=name[0]
        if len(name)>1:
            first_name = ''
            for i in range(0,len(name)-1):
                first_name+=str(name[i])+' '
            last_name = name[-1]
        
        op_admission = op_admission.create({
            'name': target_partner.name,
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'sale_id': self.id,
            'email': target_partner.email,
            'mobile': target_partner.mobile,
            'phone':target_partner.phone,
            'partner_id': target_partner.id,
            'register_id' : admission_register_id.id,
            'course_id' : admission_register_id.course_id.id,
            'application_date': fields.Datetime.now(),
            'admission_date': self.order_line.filtered(lambda l: l.product_template_id.id == admission_register_id.course_id.product_template_id.id)[:1].start_date_enroller or fields.Date.today(),
            'fees_term_id': self.env['op.fees.terms'].search([], limit=1).id,
            'gender': self.gender or target_partner.gender or 'o',
            'batch_id': self.get_lot_id(admission_register_id.course_id).id,
            'order_id': self.id,    
        })
        
        self.admission_id = op_admission.id

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    student_id = fields.Many2one(
        related='order_id.student_id',
        string='Alumno',
        readonly=True,
        store=True
    )

    def action_send_student(self):
        """
        Override para que el botón 'Inscribir' use el student_id correcto por defecto.
        Mantenemos compatibilidad con otros módulos usando super() y parcheando el contexto.
        """
        # Ejecutamos la lógica original (isep_openeducat_sale / isep_record_request)
        res = super(SaleOrderLine, self).action_send_student()
        
        # Verificamos si tenemos un estudiante explícito en el pedido
        if self.order_id.student_id:
            target_partner = self.order_id.student_id
            _logger.warning(f"ISEP_ADMISSION: action_send_student INTERCEPTANDO para Estudiante: {target_partner.name}")
            
            # Recálculo de nombre (Portado de lógica original para asegurar consistencia)
            # Limpieza básica de espacios múltiples
            clean_name = " ".join(target_partner.name.split())
            name_parts = clean_name.split(" ")
            
            first_name = ""
            last_name = ""
            
            if len(name_parts) == 1:
                first_name = name_parts[0]
            elif len(name_parts) > 1:
                first_name = " ".join(name_parts[:-1])
                last_name = name_parts[-1]

            # Actualizamos el contexto del resultado devuelto por super
            if isinstance(res, dict) and 'context' in res:
                # Aseguramos que el contexto es un dict mutable
                if not isinstance(res['context'], dict):
                    res['context'] = {} 
                
                res['context'].update({
                    'default_first_name': first_name.strip(),
                    'default_last_name': last_name.strip(),
                    'default_partner_id': target_partner.id,
                    'default_email': target_partner.email,
                    'default_mobile': target_partner.mobile,
                    'default_phone': target_partner.phone,
                })
                
        return res


