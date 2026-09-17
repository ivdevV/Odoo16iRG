import json
from odoo import fields
# Disposable DB fixture only, before installing the guard.
if 'x_studio_modalidad' not in env['sale.order.line']._fields:
    env['ir.model.fields'].create({'name':'x_studio_modalidad','field_description':'Guard test modality','model_id':env['ir.model']._get_id('sale.order.line'),'ttype':'selection','selection':'[("Online", "Online"), ("Homeclass", "Homeclass"), ("Presencial", "Presencial")]','state':'manual'})
product=env['product.product'].create({'name':'GUARD legacy product','type':'service'})
def course(code):
    v={'name':code,'code':code,'evaluation_type':'normal'}
    if 'lang' in env['op.course']._fields: v['lang']=env.user.lang or 'en_US'
    if 'name_cat' in env['op.course']._fields: v['name_cat']=code
    return env['op.course'].create(v)
c=course('GUARD-LEGACY')
a=env['op.batch'].create({'name':'Guard A','code':'GUARD-A','course_id':c.id,'start_date':fields.Date.today(),'end_date':fields.Date.today()})
b=a.copy({'name':'Guard B','code':'GUARD-B'})
d=a.copy({'name':'Guard C','code':'GUARD-C'})
pay=env['account.payment.mode'].create({'name':'Guard origin','bank_account_link':'variable','payment_method_id':env.ref('account.account_payment_method_manual_in').id})
pay2=pay.copy({'name':'Guard destination'})
ids={}
for kind in ['submitted','missing','modality','academic_approved','done','refused','race']:
    partner=env['res.partner'].create({'name':'GUARD legacy '+kind})
    student=env['op.student'].create({'partner_id':partner.id,'first_name':'Guard','last_name':kind,'gender':'o'})
    enrollment=env['op.student.course'].create({'student_id':student.id,'course_id':c.id,'batch_id':a.id,'roll_number':'GUARD-'+kind})
    ov={'partner_id':partner.id,'payment_mode_id':pay.id}
    if 'student_id' in env['sale.order']._fields: ov['student_id']=partner.id
    order=env['sale.order'].create(ov)
    env['sale.order.line'].create({'order_id':order.id,'product_id':product.id,'product_uom_qty':1,'price_unit':10,'x_studio_modalidad':'Online'})
    vals={'student_id':student.id,'student_course_id':enrollment.id,'sale_order_id':order.id,'change_batch':True,'origin_course_id':c.id,'origin_batch_id':a.id,'dest_batch_id':b.id,'origin_payment_mode_id':pay.id}
    if kind=='missing': vals['origin_batch_id']=False
    if kind=='modality': vals.update(change_modality=True,origin_modality='Online',dest_modality='Homeclass')
    if kind in ['academic_approved','race']: vals.update(change_payment=True,dest_payment_mode_id=pay2.id)
    request=env['irg.enrollment.change'].create(vals)
    if kind=='academic_approved': request.action_approve_academic()
    elif kind=='done': request.write({'state':'done'})
    elif kind=='refused': request.action_refuse()
    ids[kind]=request.id
# Real assertion on baseline: stale batch MUST remain C (currently overwritten).
r=env['irg.enrollment.change'].browse(ids['race'])
r.student_course_id.batch_id=d
r.action_approve_academic()
try:
    assert r.student_course_id.batch_id==d, 'RED expected: baseline overwrote concurrent batch C with destination B'
except AssertionError as err:
    print(str(err))
else:
    raise AssertionError('Expected RED did not fail')
r.student_course_id.batch_id=a
r.write({'state':'submitted','academic_user_id':False,'academic_date':False})
ids.update(batch_a=a.id,batch_b=b.id,batch_c=d.id,product=product.id,pay_a=pay.id,pay_b=pay2.id)
env['ir.config_parameter'].sudo().set_param('irg_guard_test_fixtures',json.dumps(ids))
env.cr.commit()
print('LEGACY fixtures committed before install:',json.dumps(ids,sort_keys=True))
