import base64
from odoo import fields, http, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.http import request
from werkzeug.exceptions import NotFound
from odoo.exceptions import ValidationError
from odoo.addons.web.controllers.binary import Binary
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.osv.expression import OR


class BinaryInh(Binary):

    @http.route('/web/content/<string:model>/<int:id>/<string:field>', type='http', auth="public")
    # pylint: disable=redefined-builtin,invalid-name
    def certificate_download(self, xmlid=None, model='ir.attachment', id=None, field='raw',
                       filename=None, filename_field='name', mimetype=None, unique=False,
                       download=False, access_token=None, nocache=False):
        attachment_id = False
        if model == 'ir.attachment':
            attachment_id = request.env[model].sudo().search([('id','=',id)])
        if attachment_id and attachment_id.certificado_web:
            user_id = request.env.user 
            student_id = request.env['op.student'].sudo().search([('user_id','=',user_id.id)], limit=1)
            certificate_log = request.env['certificate.log'].sudo()
            log_vals = {
                        'date':fields.Datetime.now(),
                        'certificate_name':attachment_id.name,
                        'download_from': 'web',
                        'user_id': request.env.user.id,
                        'student_id': student_id.id,
                        'invoice_id': attachment_id.cert_invoice_id.id
                       }
            certificate_log.create(log_vals)
        res = super().content_common(xmlid=xmlid, model=model, 
            id=id, field=field, filename=filename, filename_field=filename_field, 
            mimetype=mimetype, unique=unique, download=download, 
            access_token = access_token, nocache=nocache)
        return res




class CertificatesPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id','=',user.id)])
        Attachment = request.env['ir.attachment'].sudo()
        student_attachment_ids = Attachment.search([('res_model','=','op.student'),('res_id','=',student_id.id)])
        if 'servicios_count' in counters:
            values['servicios_count'] = 1
        if 'certificates_count' in counters:
            domain = []        
            domain += [('res_model', '=', 'op.student')]
            domain += [('id','in',student_attachment_ids.ids)]
            domain += [('certificado_web','=',True)]
            certificates_count = Attachment.sudo().search_count(domain) \
                if Attachment.sudo().check_access_rights('read', raise_exception=False) else 0
            values['certificates_count'] = certificates_count if certificates_count else '0'
        return values
    
    @http.route(['/verificar_documento'], type='http', auth="public", website=True, sitemap=False)
    def verificar_documento(self, **kw):
        if request.httprequest.method == 'GET':
            data = {}
            if kw and kw.keys():
                for val in kw.keys():
                    data[val] = kw.get(val)
            verified_values = request.env['op.sign_certificate'].sudo().web_verify_certificate(data)
            return request.render("isep_openeducat_reports.portal_verificar_documento", {'values':[verified_values]})
        return NotFound

    @http.route(['/my/certificates', '/my/certificates/page/<int:page>'], type='http', auth="user", website=True, sitemap=False)
    def portal_my_certificates(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kw):
        user = request.env.user
        new_invoice = False
        student_id = request.env['op.student'].sudo().search([('user_id','=',user.id)])

        try:
           cert_days_fpayment = int(http.request.env["ir.config_parameter"].sudo().get_param("cert_days_fpayment"))
        except ValueError:
           cert_days_fpayment = 7
        try:
           cert_days_fdownload = int(http.request.env["ir.config_parameter"].sudo().get_param("cert_days_fdownload"))
        except ValueError:
           cert_days_fdownload = 3



        if request.httprequest.method == 'POST':
            if request.params.get('titulacion') == '1':# TEMPORAL PARA ADAPTAR A NUEVO PRODUCTO DE TITULACION
                product_id = request.params.get('product_id')
                if product_id:
                    product_tmpl = request.env['product.template'].sudo().browse(int(product_id))
                    if product_tmpl and product_tmpl.website_published:
                        product_variant = product_tmpl.product_variant_id
                        if product_variant:
                            return request.redirect(f'/my/redirect_add_to_cart/{product_variant.id}')
                return request.redirect('/my/certificates')# TEMPORAL PARA ADAPTAR A NUEVO PRODUCTO DE TITULACION

            required_certificate = kw.get ('selection_value', False)
            required_batch = kw.get ('batch_value', False)
            if required_certificate:
                try:
                    required_certificate = int(required_certificate)
                except (ValueError, TypeError):
                    raise ValidationError("Valor Inválido")
                try:
                    required_batch = int(required_batch)
                except (ValueError, TypeError):
                    raise ValidationError("Valor Inválido")
 
                report_id = request.env['ir.actions.report'].sudo().search([('id', '=', required_certificate)])
                if not report_id:
                    raise ValidationError("Reporte Inválido")
                batch_id = request.env['op.batch'].sudo().search([('id', '=', required_batch)])
                if not batch_id:
                    raise ValidationError("Valor Inválido")
                
                student_course_ids = request.env['op.student.course'].sudo().search([('batch_id', '=', required_batch)])
                if batch_id not in student_course_ids.mapped('batch_id'):
                    raise ValidationError("Valor Inválido")
                #Check if certificate can be created
                access_res = report_id.check_web_available(student_id,batch_id)
                if access_res and type(access_res) == dict and 'error_message' in access_res.keys():
                    values = {'error_message': access_res.get('error_message')}
                    return request.render("isep_openeducat_reports.error_template_message", values)
                if not report_id.certificado_gratuito:
                    invoice_id = False
                    xmlids = report_id.get_external_id()
                    report_xml_id = xmlids.get(report_id.id)

                    if report_xml_id == 'isep_openeducat_reports.r_certificado7': #Título
                        #Buscar factura de título
                        subscription_data = student_id.sudo().get_subscription_data()
                        sale_order_ids = subscription_data.get('sale_order_ids', False)
                        for line in sale_order_ids.mapped('subscription_schedule.invoice_ids.invoice_line_ids'):
                            if line.product_id.is_title and line.move_id.payment_state in ['paid','in_payment']:
                                certificates = request.env['ir.attachment'].sudo().search([('cert_invoice_id','=',line.move_id.id)])
                                if not certificates: # Que la factura no esté amparando otro certificado.
                                    invoice_id = line.move_id
                                    break
                        if invoice_id:
                        #Se encontró una factura por título
                            invoice_id.certificado_web = True #Aparecer la factura en web
                            new_invoice = invoice_id
                        
                    if not invoice_id:  
                        #Generar Factura
                        certificate_product_id = request.env.company.cert_product_id.sudo()
                        invoice_line_vals={
                            'product_id':certificate_product_id.id,
                            'quantity':1.0,
                            'name': '%s. Certificado %s' %(certificate_product_id.display_name,report_id.name),
                            'price_unit': report_id.list_price or certificate_product_id.list_price,
                            }
    
                        invoice_vals={
                            'partner_id': user.partner_id.id,
                            'certificado_web': True,
                            'move_type': 'out_invoice',
                            'company_id': request.env.company.id,
                            'invoice_date': fields.Datetime.now(),
                            'invoice_date_due': fields.Datetime.now()+ timedelta(days=cert_days_fpayment),
                            'invoice_line_ids': [(0,0,invoice_line_vals)]
                            }
                        new_invoice = request.env['account.move'].sudo().create(invoice_vals)
                        if not new_invoice:
                            raise ValidationError('No se pudo solicitar el Certificado')
                        #new_invoice.action_post() 
                #Generar PDF
                data = {
                     'admissions': student_course_ids,
                     'batch_id': batch_id.sudo().id,
                     'student_ids': student_id.ids,
                     'doc_model': 'op.student',  # Odoo model name you're working with
                }
                pdf, tipo = report_id.sudo().with_context(disable_attachment=True)._render_qweb_pdf(report_id.xml_id, data=data)
                pdf_content = base64.b64encode(pdf)
                #Generar Attachment
                attach = request.env['ir.attachment'].sudo().create({
                    'name': report_id.name,
                    'type': 'binary',
                    'datas': pdf_content,
                    'store_fname': report_id.name + '.pdf',
                    'res_model': student_id._name,
                    'res_id': student_id.id,
                    'cert_invoice_id': new_invoice and new_invoice.id or False,
                    'certificado_web': True,
                    'certificado_gratuito': report_id.certificado_gratuito,
                    'mimetype': 'application/pdf'
                })

                
                #Generar Enlace de Pago
                #Redirigir a Enlace de Pago        
            return request.redirect('/my/certificates')


        

        values = self._prepare_portal_layout_values()
        Attachment = request.env['ir.attachment'].sudo()
        student_attachment_ids = Attachment.search([('res_model','=','op.student'),('res_id','=',student_id.id)])
        domain = [
            ('res_model', '=', 'op.student'),
            ('id','in',student_attachment_ids.ids),
            ('certificado_web','=',True)
            ]        
        
        
        searchbar_sortings = {
            'date': {'label': _('Nuevo'), 'order': 'id desc'},
            'name': {'label': _('Nombre'), 'order': 'name asc, id asc'},
        }
        
        # default sortby order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        
        searchbar_inputs = {
            'all': {'input': 'all', 'label': _('Buscar en todo')},
            'name': {'input': 'name', 'label': _('Buscar en nombre')},
            'description': {'input': 'description', 'label': _('Buscar en descripción')},
        }
        
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
        }
        
        # search
        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('description', 'all'):
                search_domain = OR([search_domain, [('description', 'ilike', search)]])            
            domain += search_domain
    
        # count for pager
        certificates_count = Attachment.search_count(domain)
        
        # default filter by value
        if not filterby:
            filterby = 'all'
        
        # make pager
        pager = portal_pager(
            url="/my/certificates",
            url_args={'sortby': sortby, 'filterby': filterby, 'groupby': groupby, 'search_in': search_in, 'search': search},
            total=certificates_count,
            page=page,
            step=self._items_per_page
        )
        
        # search the certificates to display, according to the pager data
        certificates = Attachment.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        
        grouped_certificates = []
        if certificates:
            grouped_certificates = [certificates]
        
        
        product_ids = request.env['product.template'].sudo().search([('active', '=', True), ('view_titulacion', '=', True), ('website_published', '=', True)]) # TEMPORAL PARA ADAPTAR A NUEVO PRODUCTO DE TITULACION

        request.session['my_certificates_history'] = certificates.ids[:100]
        certificate_ids = http.request.env['ir.actions.report'].sudo().search([('model','ilike','%op.student%'),('certificado_web','=',True)])
        batch_ids = request.env['op.student.course'].sudo().search([('student_id','=',student_id.id)]).mapped('batch_id')
        values.update({
            'certificate_ids': certificate_ids.sudo(),
            'batch_ids': batch_ids.sudo(),
            'certificates': certificates.sudo(),
            'grouped_certificates': grouped_certificates,
            'page_name': 'Certificados',
            'default_url': '/my/certificates',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'filterby': filterby,                        
            'cert_days_fpayment': cert_days_fpayment,
            'cert_days_fdownload': cert_days_fdownload,
            'base_url': http.request.env["ir.config_parameter"].sudo().get_param("web.base.url"),
            'product_ids': product_ids, # TEMPORAL PARA ADAPTAR A NUEVO PRODUCTO DE TITULACION
        })
        return request.render("isep_openeducat_reports.portal_my_certificates", values)
        
    
    @http.route(['/new_payment_link/<int:attachment>'], type='http', auth="user", website=True, sitemap=False)
    def new_payment_link(self, **kw):
        att_id = kw.get('attachment', False)
        if att_id:
            user = request.env.user
            student_id = request.env['op.student'].sudo().search([('user_id','=',user.id)])
            attachment_id = request.env['ir.attachment'].sudo().search([('id','=',int(att_id))], limit = 1)
            if attachment_id.res_id == student_id.id and attachment_id.cert_invoice_id and attachment_id.cert_invoice_id.payment_state != 'paid':
                payment_link_id = request.env['payment.link.wizard'].sudo().with_context(active_model = 'account.move', active_id = attachment_id.cert_invoice_id.id).create({})
                if payment_link_id and payment_link_id.link :
                    return request.redirect(payment_link_id.link)
        return request.redirect('/my/certificates')


    @http.route('/my/redirect_add_to_cart/<int:product_id>', type='http', auth='user', website=True)
    def redirect_add_to_cart(self, product_id, **kw):
        import logging
        _logger = logging.getLogger(__name__)
        
        # Verificar si es product.product o product.template
        product_variant = request.env['product.product'].sudo().browse(product_id)
        product_template = request.env['product.template'].sudo().browse(product_id)
        
        _logger.info(f"redirect_add_to_cart called with ID: {product_id}")
        
        if product_variant.exists():
            _logger.info(f"Found as product.product: {product_variant.name}")
            final_product_id = product_id
        elif product_template.exists():
            _logger.info(f"Found as product.template: {product_template.name}")
            if product_template.product_variant_ids:
                final_product_id = product_template.product_variant_ids[0].id
                _logger.info(f"Using first variant: {product_template.product_variant_ids[0].name} (ID: {final_product_id})")
            else:
                _logger.error(f"No variants found for template {product_id}")
                return request.redirect('/my/p_other_services?error=no_variants')
        else:
            _logger.error(f"Product ID {product_id} not found as variant or template")
            return request.redirect('/my/p_other_services?error=product_not_found')
        
        # Procesar campos personalizados si vienen de variantes
        variant_text = kw.get('variant_text', '')
        if variant_text:
            import re
            from datetime import datetime, timedelta
            from dateutil.relativedelta import relativedelta
            
            # Extraer número de cuotas del texto (ej: "16 cuotas" -> 16, "contado" -> 1)
            match = re.search(r'(\d+)', variant_text)
            term_number = int(match.group(1)) if match else 1  # Default 1 si no encuentra número
            _logger.info(f"Extracted term_number: {term_number} from variant_text: {variant_text}")
            
            # Si hay cuotas (más de 1), crear orden directa
            if term_number >= 1:
                _logger.info(f"Creating direct order for installments with {term_number} terms")
                
                # Buscar recurrencia mensual
                recurrence = request.env['sale.temporal.recurrence'].sudo().search([
                    ('unit', '=', 'month'),
                    ('duration', '=', 1)
                ], limit=1)
                
                if not recurrence:
                    _logger.error("No monthly recurrence found")
                    return request.redirect('/my/p_other_services?error=no_recurrence')
                
                # Calcular fechas
                start_date = datetime.now().date()
                end_date = start_date + relativedelta(months=term_number) - timedelta(days=1)
                
                # Crear orden directa para cuotas
                order = request.env['sale.order'].sudo().create({
                    'partner_id': request.env.user.partner_id.id,
                    'partner_invoice_id': request.env.user.partner_id.id,
                    'partner_shipping_id': request.env.user.partner_id.id,
                    'company_id': request.env.company.id,
                    'currency_id': request.env.company.currency_id.id,
                    'term_number_id': 8,
                    'term_number': term_number,
                    'recurrence_id': recurrence.id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_subscription': True
                })
                
                # Agregar línea de producto
                request.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'product_id': final_product_id,
                    'product_uom_qty': 1,
                    'price_unit': request.env['product.product'].sudo().browse(final_product_id).list_price
                })
                
                _logger.info(f"Direct order {order.name} created with product {final_product_id}")
                
                # Ejecutar onchange para calcular end_date correctamente
                order.onchange_end_date_suscrip()
                
                # Confirmar la orden para generar cronograma
                order.action_confirm()
                _logger.info(f"Order {order.name} confirmed")
                
                # Marcar productos como entregados para poder facturar
                for line in order.order_line:
                    if line.product_id.type == 'service':
                        line.qty_delivered = line.product_uom_qty
                
                # Crear factura
                try:
                    invoice = order._create_invoices()
                    if invoice:
                        _logger.info(f"Invoice {invoice.name} created for order {order.name}")
                        
                        # Publicar la factura (confirmarla)
                        invoice.action_post()
                        _logger.info(f"Invoice {invoice.name} posted")
                        
                        # Asociar factura al primer cronograma
                        if order.subscription_schedule:
                            first_schedule = order.subscription_schedule[0]
                            invoice.schedule_id = first_schedule.id
                            _logger.info(f"Invoice {invoice.name} associated to schedule {first_schedule.name}")
                        
                        # Crear enlace de pago para la factura
                        payment_link = request.env['payment.link.wizard'].sudo().with_context(
                            active_model='account.move', 
                            active_id=invoice.id
                        ).create({})
                        
                        if payment_link and payment_link.link:
                            _logger.info(f"Payment link created for invoice {invoice.name}: {payment_link.link}")
                            return request.redirect(payment_link.link)
                        else:
                            _logger.error(f"Failed to create payment link for invoice {invoice.name}")
                            return request.redirect('/my/p_other_services?error=payment_link_failed')
                    else:
                        _logger.error(f"No invoice created for order {order.name}")
                        return request.redirect('/my/p_other_services?error=no_invoice_created')
                except Exception as e:
                    _logger.error(f"Error creating/posting invoice for order {order.name}: {str(e)}")
                    return request.redirect('/my/p_other_services?error=invoice_process_failed')
        
        # Flujo normal: agregar al carrito
        _logger.info(f"Adding to cart product ID: {final_product_id}")
        order = request.website.sale_get_order(force_create=True)
        order._cart_update(product_id=final_product_id, add_qty=1)
        
        # Flujo normal para productos sin cuotas
        return request.redirect("/shop/payment")

    @http.route(['/my/get_product_variants/<int:product_id>'], type='json', auth='user', website=True)
    def get_product_variants(self, product_id, **kw):
        """Obtener variantes de un producto"""
        try:
            variants = request.env['product.template.attribute.value'].sudo().search([
                ('product_tmpl_id', '=', product_id)
            ])
            
            variant_data = []
            for variant in variants:
                variant_data.append({
                    'id': variant.id,
                    'name': variant.name,
                    'attribute_name': variant.attribute_id.name,
                    'product_variant_ids': [pv.id for pv in variant.ptav_product_variant_ids]
                })
            
            return variant_data
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f"Error getting product variants for product {product_id}: {str(e)}")
            return []

    @http.route(['/my/get_product_variant_id/<int:product_id>'], type='json', auth='user', website=True)
    def get_product_variant_id(self, product_id, **kw):
        """Obtener el product_variant_id de un product.template"""
        import logging
        _logger = logging.getLogger(__name__)
        try:
            product_template = request.env['product.template'].sudo().browse(product_id)
            _logger.info(f"Getting variant for product template ID: {product_id}, name: {product_template.name}")
            if product_template.exists() and product_template.product_variant_ids:
                variant_id = product_template.product_variant_ids[0].id
                variant_name = product_template.product_variant_ids[0].name
                _logger.info(f"Found variant ID: {variant_id}, name: {variant_name}")
                return {'variant_id': variant_id}
            _logger.warning(f"No variants found for product template {product_id}")
            return {'variant_id': None}
        except Exception as e:
            _logger.error(f"Error getting product variant id for product {product_id}: {str(e)}")
            return {'variant_id': None}

    @http.route(['/my/servicios_academicos'], type='http', auth="user", website=True,sitemap=False)
    def portal_menu_servicioss(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kw):
        servicios_count = 1
        return request.render("isep_openeducat_reports.portal_servicios_academicos", {
            'servicios_count': servicios_count
        })
        

    @http.route(['/my/titulaciones'], type='http', auth="user", website=True)
    def portal_titulaciones(self, **kw):
        user = request.env.user
        partner_id = user.partner_id.id
        
        # Buscar órdenes de venta del cliente que sean de titulación
        SaleOrderLine = request.env['sale.order.line'].sudo()
        PaymentTransaction = request.env['payment.transaction'].sudo()
        
        # Obtener las líneas de venta de titulación
        domain = [
            ('order_partner_id', '=', partner_id),
            ('product_template_id.view_titulacion', '=', True),
            ('state', 'in', ['sale', 'done'])
        ]
        
        sale_lines = SaleOrderLine.search(domain)
        
        # Preparar la información de pagos
        payment_info = []
        for line in sale_lines:
            # Buscar transacciones de pago relacionadas con esta orden
            transactions = PaymentTransaction.search([
                ('reference', 'ilike', line.order_id.name)
            ])
            
            # Si no hay transacciones, buscar información del cronograma
            schedule_info = None
            if not transactions and line.order_id.subscription_schedule:
                total_schedules = len(line.order_id.subscription_schedule)
                paid_schedules = len(line.order_id.subscription_schedule.filtered(lambda s: s.payment_state == 'paid'))
                schedule_info = f"De {total_schedules} cuotas {paid_schedules} pagada{'s' if paid_schedules != 1 else ''}"
            
            payment_info.append({
                'order_name': line.order_id.name,
                'product_name': line.product_id.name,
                'amount': line.price_total,
                'currency_id': line.currency_id,
                'order_date': line.order_id.date_order,
                'state': line.order_id.state,
                'schedule_info': schedule_info,
                'transactions': [{
                    'reference': t.reference,
                    'amount': t.amount,
                    'currency_id': t.currency_id,
                    'state': t.state,
                    'date': t.create_date
                } for t in transactions]
            })

        # Productos disponibles para comprar con sus variantes
        products = request.env['product.template'].sudo().search([
            ('active', '=', True),
            ('view_titulacion', '=', True),
            ('website_published', '=', True)
        ], order='display_name asc')
        
        # Obtener variantes de productos
        product_variants = {}
        for product in products:
            variants = request.env['product.template.attribute.value'].sudo().search([
                ('product_tmpl_id', '=', product.id)
            ])
            if variants:
                product_variants[product.id] = True
        
        return request.render("isep_openeducat_reports.portal_titulaciones", {
            'product_ids': products,
            'product_variants': product_variants,
            'payment_info': payment_info
        })

    @http.route(['/my/p_practices'], type='http', auth="user", website=True)
    def portal_practicas(self, **kw):
        user = request.env.user
        partner_id = user.partner_id.id

        # Buscar órdenes de venta del cliente que sean de prácticas
        SaleOrderLine = request.env['sale.order.line'].sudo()
        PaymentTransaction = request.env['payment.transaction'].sudo()

        # Obtener las líneas de venta de prácticas  
        domain = [
            ('order_partner_id', '=', partner_id),
            ('product_template_id.view_practices', '=', True),
            ('state', 'in', ['sale', 'done'])
        ]
        
        sale_lines = SaleOrderLine.search(domain)
        
        # Preparar la información de pagos
        payment_info = []
        for line in sale_lines:
            # Buscar transacciones de pago relacionadas con esta orden
            transactions = PaymentTransaction.search([
                ('reference', 'ilike', line.order_id.name)
            ])
            
            # Si no hay transacciones, buscar información del cronograma
            schedule_info = None
            if not transactions and line.order_id.subscription_schedule:
                total_schedules = len(line.order_id.subscription_schedule)
                paid_schedules = len(line.order_id.subscription_schedule.filtered(lambda s: s.payment_state == 'paid'))
                schedule_info = f"De {total_schedules} cuotas {paid_schedules} pagada{'s' if paid_schedules != 1 else ''}"
            
            payment_info.append({
                'order_name': line.order_id.name,
                'product_name': line.product_id.name,
                'amount': line.price_total,
                'currency_id': line.currency_id,
                'order_date': line.order_id.date_order,
                'state': line.order_id.state,
                'schedule_info': schedule_info,
                'transactions': [{
                    'reference': t.reference,
                    'amount': t.amount,
                    'currency_id': t.currency_id,
                    'state': t.state,
                    'date': t.create_date
                } for t in transactions]
            })

        # Productos disponibles para comprar con sus variantes
        products = request.env['product.template'].sudo().search([
            ('active', '=', True),
            ('view_practices', '=', True),
            ('website_published', '=', True)
        ], order='display_name asc')
        
        # Obtener variantes de productos
        product_variants = {}
        for product in products:
            variants = request.env['product.template.attribute.value'].sudo().search([
                ('product_tmpl_id', '=', product.id)
            ])
            if variants:
                product_variants[product.id] = True
        
        return request.render("isep_openeducat_reports.portal_p_practicas", {
            'product_ids': products,
            'product_variants': product_variants,
            'payment_info': payment_info
        })

    @http.route(['/my/p_other_services'], type='http', auth="user", website=True)
    def portal_other_services(self, **kw):
        user = request.env.user
        partner_id = user.partner_id.id

        # Buscar órdenes de venta del cliente que sean otros servicios
        SaleOrderLine = request.env['sale.order.line'].sudo()
        PaymentTransaction = request.env['payment.transaction'].sudo()

        # Obtener las líneas de venta de otros servicios
        domain = [
            ('order_partner_id', '=', partner_id),
            ('product_template_id.view_other', '=', True),
            ('state', 'in', ['sale', 'done'])
        ]
        
        sale_lines = SaleOrderLine.search(domain)
        
        # Preparar la información de pagos
        payment_info = []
        for line in sale_lines:
            # Buscar transacciones de pago relacionadas con esta orden
            transactions = PaymentTransaction.search([
                ('reference', 'ilike', line.order_id.name)
            ])
            
            # Si no hay transacciones, buscar información del cronograma
            schedule_info = None
            if not transactions and line.order_id.subscription_schedule:
                total_schedules = len(line.order_id.subscription_schedule)
                paid_schedules = len(line.order_id.subscription_schedule.filtered(lambda s: s.payment_state == 'paid'))
                schedule_info = f"De {total_schedules} cuotas {paid_schedules} pagada{'s' if paid_schedules != 1 else ''}"
            
            payment_info.append({
                'order_name': line.order_id.name,
                'product_name': line.product_id.name,
                'amount': line.price_total,
                'currency_id': line.currency_id,
                'order_date': line.order_id.date_order,
                'state': line.order_id.state,
                'schedule_info': schedule_info,
                'transactions': [{
                    'reference': t.reference,
                    'amount': t.amount,
                    'currency_id': t.currency_id,
                    'state': t.state,
                    'date': t.create_date
                } for t in transactions]
            })

        # Productos disponibles para comprar con sus variantes
        products = request.env['product.template'].sudo().search([
            ('active', '=', True),
            ('view_other', '=', True),
            ('website_published', '=', True)
        ], order='display_name asc')
        
        # Obtener variantes de productos
        product_variants = {}
        for product in products:
            variants = request.env['product.template.attribute.value'].sudo().search([
                ('product_tmpl_id', '=', product.id)
            ])
            if variants:
                product_variants[product.id] = True
        
        return request.render("isep_openeducat_reports.portal_p_other_services", {
            'product_ids': products,
            'product_variants': product_variants,
            'payment_info': payment_info
        })
