# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_or_get_admission(self, line):
        # Primero invocamos a super, aunque sabemos que el método original en 
        # isep_sale_order_admissions hace el create inmediatamente y retorna.
        # Por lo tanto, necesitamos sobrescribir la lógica si queremos interceptarla ANTES de crear.
        
        # Como no podemos "injectar" la variable en el método original de 'isep_sale_order_admissions',
        # tenemos que replicar la lógica modificada aquí (Override).
        
        # Copia de la lógica de _create_or_get_admission adaptada:
        
        domain = ['|', 
                 ('product_template_id', '=', line.product_template_id.id),
                 ('product_template_ids', 'in', line.product_template_id.id)]
        
        course = self.env['op.course'].search(domain, limit=1)
        
        if not course:
            self._upsert_admission_row(
                line,
                error_msg=f"No se encontró Curso para {line.product_template_id.display_name}.",
            )
            return False

        if not self.period:
            self._compute_period()
        if not self.period:
            self._upsert_admission_row(
                line,
                course=course,
                error_msg="No se pudo determinar el Periodo de Admisión.",
            )
            return False

        register = self._find_or_create_register(
            period=self.period,
            product_template=line.product_template_id,
            course=course,
        )

        admission = line.admission_id
        if not admission:
            # --- MODIFICACIÓN: Usar student_id (definido en irg_sale_order_extended) o partner_id ---
            target_partner = self.student_id or self.partner_id
            
            parts = (target_partner.name or '').split()
            first_name = ' '.join(parts[:-1]) if len(parts) > 1 else (parts[0] if parts else '-')
            last_name = parts[-1] if len(parts) > 1 else '-'

            admission = self.env['op.admission'].create({
                'name': target_partner.name,
                'first_name': (first_name or '-').strip(),
                'last_name': (last_name or '-').strip(),
                'sale_id': self.id,
                'email': target_partner.email,
                'mobile': target_partner.mobile,
                'phone': target_partner.phone,
                'partner_id': target_partner.id,
                'register_id': register.id,
                'course_id': register.course_id.id,
                'application_date': fields.Datetime.now(),
                'admission_date': fields.Datetime.now(),
                'fees_term_id': self.env['op.fees.terms'].search([], limit=1).id,
                'gender': self.gender or target_partner.gender or 'o',
                'batch_id': self.get_lot_id(course).id,
                'order_id': self.id,
            })
            line.admission_id = admission.id

        return admission


    def create_admission_manual(self, admission_register_id):
        # Override para usar student_id en creación manual
        op_admission = self.env['op.admission']
        
        # --- MODIFICACIÓN: Usar student_id ---
        target_partner = self.student_id or self.partner_id

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
            'admission_date': fields.Datetime.now(),
            'fees_term_id': self.env['op.fees.terms'].search([], limit=1).id,
            'gender': self.gender or target_partner.gender or 'o',
            'batch_id': self.get_lot_id(admission_register_id.course_id).id,
            'order_id': self.id,    
        })
        
        self.admission_id = op_admission.id
